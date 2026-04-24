import pandas as pd
from django.db import transaction
from io import BytesIO
from fastapi import HTTPException
from django.utils import timezone

from api.excel_upload.platform_factory import SettlementPlatformFactory
from orders.models import Order
from payments.models import OrderSettlement
from orders_status.models import OrderStatus


def clean_number(value):
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    try:
        return float(value)
    except Exception:
        return 0

def normalize_sub_order(val):
    if pd.isna(val):
        return ""

    val = str(val).strip()

    # remove .0 issue
    if val.endswith(".0"):
        val = val[:-2]

    return val

# ✅ STATUS LOGIC
def derive_order_status(row, mapping):
    live_status = str(row.get(mapping.get("live_status"), "")).lower()

    sale = clean_number(row.get(mapping.get("total_sale_amount")))
    ret = clean_number(row.get(mapping.get("total_return_amount")))
    final_amt = clean_number(row.get(mapping.get("final_settlement_amount")))

    # ✅ RTO
    if "rto" in live_status:
        return "RTO_COMPLETE"

    # ✅ CUSTOMER RETURN
    if "return" in live_status or ret < 0:
        return "CUSTOMER_RETURN"

    # ✅ DELIVERED
    if "delivered" in live_status and final_amt > 0:
        return "DELIVERED"

    # ✅ CANCELLED
    if final_amt == 0 and sale == 0:
        return "CANCELLED"

    return "DELIVERED"


# ✅ CLAIM LOGIC
def extract_claim_data(row, mapping):
    claims = clean_number(row.get(mapping.get("claims")))
    compensation = clean_number(row.get(mapping.get("compensation")))
    recovery = clean_number(row.get(mapping.get("recovery")))
    return claims, compensation, recovery


class SettlementUploadController:

    @staticmethod
    @transaction.atomic
    def upload_settlement_excel(file, current_user, platform_code):
        try:
            platform = SettlementPlatformFactory.get_platform(platform_code)

            file.seek(0)
            file_content = file.read()

            # ✅ Read Excel
            try:
                df = pd.read_excel(BytesIO(file_content), sheet_name=1, header=1)
            except Exception:
                df = pd.read_excel(BytesIO(file_content), sheet_name=1, header=0)

            df.columns = df.columns.astype(str).str.strip().str.replace("\n", " ")

            column_mapping = platform.detect_columns(df.columns)

            if not column_mapping.get("sub_order_id"):
                raise HTTPException(status_code=400, detail="Sub Order No column not found")

            df = df.dropna(subset=[column_mapping["sub_order_id"]])

            sub_orders = df[column_mapping["sub_order_id"]].astype(str).str.strip().tolist()

            # ✅ Fetch Orders
            orders = {
                o.marketplace_sub_order_id: o
                for o in Order.objects.filter(marketplace_sub_order_id__in=sub_orders)
            }

            # ✅ Existing settlements
            existing = {
                s.order_id: s
                for s in OrderSettlement.objects.filter(order__marketplace_sub_order_id__in=sub_orders)
            }

            # ✅ Status cache
            status_cache = {
                s.code.upper(): s
                for s in OrderStatus.objects.all()
            }

            created = []
            updated = []
            skipped = 0
            skipped_details = []

            for idx, row in df.iterrows():
                sub_order = None
                try:
                    sub_order = normalize_sub_order(row[column_mapping["sub_order_id"]])
                    # sub_order = str(row[column_mapping["sub_order_id"]]).strip()
                    excel_ids = set([normalize_sub_order(x) for x in df[column_mapping["sub_order_id"]]])

                    db_ids = set(orders.keys())

                    missing_ids = excel_ids - db_ids

                    print("❌ Missing in DB:", list(missing_ids)[:10])
                    print("✅ Found in DB:", len(db_ids))
                    print("📊 Excel total:", len(excel_ids))

                    if not sub_order:
                        skipped += 1
                        skipped_details.append({
        "row": idx + 2,
        "reason": "Missing Sub Order ID"
    })
                        continue

                    order = orders.get(sub_order)
                    if not order:
                        skipped += 1
                        skipped_details.append({
        "row": idx + 2,
        "sub_order": sub_order,
        "reason": "Order not found in DB"
    })
                        continue

                    # ✅ STATUS
                    status_name = derive_order_status(row, column_mapping)
                    status_obj = status_cache.get(status_name)

                    # ✅ CLAIMS
                    claims, compensation, recovery = extract_claim_data(row, column_mapping)

                    # ✅ FINAL AMOUNT FIX
                    final_amt = clean_number(
                        row.get(column_mapping.get("final_settlement_amount"))
                    )

                    net_amount = final_amt + compensation + claims - recovery

                    # ✅ DATA
                    data = {
                        "transaction_id": row.get(column_mapping.get("transaction_id")),
                        "payment_date": pd.to_datetime(
                            row.get(column_mapping.get("payment_date")),
                            errors="coerce"
                        ),

                        "final_settlement_amount": net_amount,
                        "total_sale_amount": clean_number(row.get(column_mapping.get("total_sale_amount"))),
                        "total_return_amount": clean_number(row.get(column_mapping.get("total_return_amount"))),

                        "fixed_fee": clean_number(row.get(column_mapping.get("fixed_fee"))),
                        "warehousing_fee": clean_number(row.get(column_mapping.get("warehousing_fee"))),
                        "return_premium": clean_number(row.get(column_mapping.get("return_premium"))),
                        "return_premium_return": clean_number(row.get(column_mapping.get("return_premium_return"))),

                        "gst_percent": clean_number(row.get(column_mapping.get("gst_percent"))),

                        "extra_data": {
                            "claims": claims,
                            "compensation": compensation,
                            "recovery": recovery,
                        },

                        "created_by": current_user
                    }

                    # ✅ CREATE / UPDATE SETTLEMENT
                    settlement = existing.get(order.id)

                    if settlement:
                        for k, v in data.items():
                            setattr(settlement, k, v)
                        updated.append(settlement)
                    else:
                        created.append(OrderSettlement(order=order, **data))

                    # ✅ UPDATE ORDER STATUS
                    if status_obj and order.status != status_obj:
                        order.status = status_obj
                        order.status_updated_at = timezone.now()
                        order.save(update_fields=["status", "status_updated_at"])

                except Exception as e:
                    skipped += 1
                    skipped_details.append({
                        "row": idx + 2,
                        "sub_order": sub_order,
                        "error": str(e)
                    })

            if created:
                OrderSettlement.objects.bulk_create(created, batch_size=500)

            if updated:
                OrderSettlement.objects.bulk_update(
                    updated,
                    [
                        "transaction_id",
                        "payment_date",
                        "final_settlement_amount",
                        "total_sale_amount",
                        "total_return_amount",
                        "fixed_fee",
                        "warehousing_fee",
                        "return_premium",
                        "return_premium_return",
                        "gst_percent",
                        "extra_data",
                    ],
                    batch_size=500
                )

            return {
                "message": "Settlement uploaded successfully",
                "created": len(created),
                "updated": len(updated),
                "skipped": skipped,
                "skipped_details": skipped_details
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))