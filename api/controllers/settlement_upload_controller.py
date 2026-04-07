# payments/controllers/settlement_upload_controller.py

import pandas as pd
from django.db import transaction
from io import BytesIO
from fastapi import HTTPException

from api.excel_upload.platform_factory import SettlementPlatformFactory
from orders.models import Order
from payments.models import OrderSettlement


def clean_number(value):
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    try:
        return float(value)
    except Exception:
        return 0


class SettlementUploadController:

    @staticmethod
    @transaction.atomic
    def upload_settlement_excel(file, current_user, platform_code):
        try:
            platform = SettlementPlatformFactory.get_platform(platform_code)

            file.seek(0)
            file_content = file.read()

            # Try reading Excel with header=1 (second row)
            try:
                df = pd.read_excel(BytesIO(file_content), sheet_name=1, header=1)
            except ValueError as ve:
                # If only one row exists, fallback to header=0
                if "len of 1" in str(ve):
                    df = pd.read_excel(BytesIO(file_content), sheet_name=1, header=0)
                else:
                    raise HTTPException(status_code=400, detail=f"Failed to read Excel: {str(ve)}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read Excel: {str(e)}")

            # Clean column names
            df.columns = df.columns.astype(str).str.strip().str.replace("\n", " ")

            # DEBUG: print detected columns
            # print("Detected columns:", df.columns.tolist())

            # Detect platform-specific columns
            column_mapping = platform.detect_columns(df.columns)

            if not column_mapping.get("sub_order_id"):
                raise HTTPException(
                    status_code=400,
                    detail="Sub Order No column not found in Excel file"
                )

            # Drop rows where sub_order_id is missing
            df = df.dropna(subset=[column_mapping["sub_order_id"]])

            sub_orders = df[column_mapping["sub_order_id"]].astype(str).str.strip().tolist()

            # Fetch orders from database
            orders = {
                o.marketplace_sub_order_id: o
                for o in Order.objects.filter(marketplace_sub_order_id__in=sub_orders)
            }
            print(df[column_mapping["sub_order_id"]].value_counts().head(10))
            # Existing settlements for update
            existing = {
                s.order_id: s
                for s in OrderSettlement.objects.filter(order__marketplace_sub_order_id__in=sub_orders)
            }

            created = []
            updated = []
            skipped = 0
            skipped_details = []

            for idx, row in df.iterrows():
                sub_order = None
                try:
                    sub_order = str(row[column_mapping["sub_order_id"]]).strip()

                    if not sub_order:
                        skipped += 1
                        skipped_details.append({
                            "row": idx + 2,
                            "reason": "Missing Sub Order No"
                        })
                        continue

                    order = orders.get(sub_order)
                    if not order:
                        skipped += 1
                        skipped_details.append({
                            "row": idx + 2,
                            "sub_order": sub_order,
                            "reason": "Order not found"
                        })
                        continue

                    data = {
                        "transaction_id": row.get(column_mapping.get("transaction_id")),
                        "payment_date": pd.to_datetime(
                            row.get(column_mapping.get("payment_date")), errors="coerce"
                        ),
                        "final_settlement_amount": clean_number(
                            row.get(column_mapping.get("final_settlement_amount"))
                        ),
                        "total_sale_amount": clean_number(
                            row.get(column_mapping.get("total_sale_amount"))
                        ),
                        "total_return_amount": clean_number(
                            row.get(column_mapping.get("total_return_amount"))
                        ),
                        "fixed_fee": clean_number(
                            row.get(column_mapping.get("fixed_fee"))
                        ),
                        "warehousing_fee": clean_number(
                            row.get(column_mapping.get("warehousing_fee"))
                        ),
                        "return_premium": clean_number(
                            row.get(column_mapping.get("return_premium"))
                        ),
                        "return_premium_return": clean_number(
                            row.get(column_mapping.get("return_premium_return"))
                        ),
                        "gst_percent": clean_number(
                            row.get(column_mapping.get("gst_percent"))
                        ),
                        "created_by": current_user
                    }

                    settlement = existing.get(order.id)

                    if settlement:
                        # Update existing
                        for k, v in data.items():
                            setattr(settlement, k, v)
                        updated.append(settlement)
                    else:
                        # Create new
                        created.append(OrderSettlement(order=order, **data))

                except Exception as row_error:
                    skipped += 1
                    skipped_details.append({
                        "row": idx + 2,
                        "sub_order": sub_order,
                        "reason": f"Row processing error: {str(row_error)}"
                    })

            # Bulk create/update
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

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Settlement upload failed: {str(e)}"
            )