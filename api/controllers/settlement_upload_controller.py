import uuid

import pandas as pd
from django.db import transaction
from io import BytesIO
from fastapi import HTTPException
from django.utils import timezone

from adsSpend.models import AdsSpend
from api.controllers.profit_controller import ProfitCalculationService
from api.excel_upload.platform_factory import SettlementPlatformFactory
from categories.models import Category
from customers.models import Customer
from marketplace.models import MarketplaceOrder
from orders.models import Order
from payments.models import OrderSettlement
from orders_status.models import OrderStatus
from platforms.models import Platform
from products.models import Product, ProductVariant


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
    claims = clean_number(row.get(mapping.get("claims")))

    # ✅ RTO
    if "rto" in live_status:
        return "RTO_COMPLETE"

    # ✅ CUSTOMER RETURN
    if "return" in live_status or ret < 0:
        return "CUSTOMER_RETURN"
    # ✅ CUSTOMER RETURN for claims
    if not live_status and claims > 0:
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
            platform_obj = Platform.objects.filter(code=platform_code).first()
            if not platform_obj:
                raise HTTPException(status_code=400, detail="Invalid platform code")
            
            products_created = 0
            variants_created = 0
            orders_created = 0
            customers_created = 0

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
            # orders = {
            #     o.marketplace_sub_order_id: o
            #     for o in Order.objects.filter(marketplace_sub_order_id__in=sub_orders)
            # }
            orders = {
                o.marketplace_sub_order_id: o
                for o in Order.objects.filter(
                    marketplace_sub_order_id__in=sub_orders) }

            variants_cache = {
                v.sku.upper(): v
                for v in ProductVariant.objects.select_related("product")
            }
            customer_cache = {}

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
            # ==========================================
            # ADS COST SHEET
            # ==========================================
            ads_records = []
            existing_ads = []
            existing_set = set()
            new_records = []
            try:
                df_ads = pd.read_excel(
                    BytesIO(file_content),
                    sheet_name="Ads Cost",
                    header=1
                )
                

                df_ads.columns = (
                    df_ads.columns
                    .astype(str)
                    .str.strip()
                    .str.replace("\n", " ", regex=False)
                )

                # print("ADS COLUMNS:", df_ads.columns.tolist())
                # print("ADS ROWS:", len(df_ads))

                # Optional: remove old ads spend records for this platform
                # AdsSpend.objects.filter(platform=platform_obj).delete()

                for _, row in df_ads.iterrows():

                    campaign_id = row.get("Campaign ID")

                    if pd.isna(campaign_id):
                        continue

                    campaign_id = str(campaign_id).strip()

                    if not campaign_id:
                        continue

                    deduction_duration = None
                    deduction_date = None

                    if pd.notna(row.get("Deduction Duration")):
                        deduction_duration = pd.to_datetime(
                            row.get("Deduction Duration"),
                            errors="coerce"
                        )

                    if pd.notna(row.get("Deduction Date")):
                        deduction_date = pd.to_datetime(
                            row.get("Deduction Date"),
                            errors="coerce"
                        )

                    ads_records.append(
                        AdsSpend(
                            platform=platform_obj,
                            campaign_id=campaign_id,

                            deduction_duration=deduction_duration,
                            deduction_date=deduction_date,

                            ad_cost=clean_number(
                                row.get("Ad Cost")
                            ),

                            credits=clean_number(
                                row.get("Credits / Waivers / Discounts")
                            ),

                            ad_cost_after_adjustment=clean_number(
                                row.get(
                                    "Ad Cost incl. Credits/Waivers/Discounts"
                                )
                            ),

                            gst=clean_number(
                                row.get("GST")
                            ),

                            total_ads_cost=abs(
                                clean_number(
                                    row.get("Total Ads Cost")
                                )
                            ),

                            created_by=current_user
                        )
                    )

                print("ADS RECORDS TO INSERT:", len(ads_records))
                

                if ads_records:
                    existing_ads = AdsSpend.objects.filter(
                    platform=platform_obj,
                    campaign_id__in=[r.campaign_id for r in ads_records]
                ).values("campaign_id", "deduction_duration")

                existing_set = {
                    (x["campaign_id"], x["deduction_duration"])
                    for x in existing_ads
                }

                new_records = [
                    r for r in ads_records
                    if (r.campaign_id, r.deduction_duration.date() if r.deduction_duration else None)
                    not in existing_set
                ]

                AdsSpend.objects.bulk_create(new_records, batch_size=1000)

            except Exception as e:
                print("ADS COST ERROR:", str(e))
                raise HTTPException(
                    status_code=400,
                    detail=f"Ads Cost Import Error: {str(e)}"
                )
            for idx, row in df.iterrows():
                sub_order = None
                try:
                    sub_order = normalize_sub_order(row[column_mapping["sub_order_id"]])
                    # sub_order = str(row[column_mapping["sub_order_id"]]).strip()
                    # excel_ids = set([normalize_sub_order(x) for x in df[column_mapping["sub_order_id"]]])

                    # db_ids = set(orders.keys())

                    # missing_ids = excel_ids - db_ids

                    # print("❌ Missing in DB:", list(missing_ids)[:10])
                    # print("✅ Found in DB:", len(db_ids))
                    # print("📊 Excel total:", len(excel_ids))

                    if not sub_order:
                        skipped += 1
                        skipped_details.append({
                            "row": idx + 2,
                            "reason": "Missing Sub Order ID"
                        })
                        continue

                    # order = orders.get(sub_order)
                    # if not order:
                    #     skipped += 1
                    #     skipped_details.append({
                    #             "row": idx + 2,
                    #             "sub_order": sub_order,
                    #             "reason": "Order not found in DB"
                    #         })
                    #     continue
                    order = orders.get(sub_order)
                    if not order:
                        result = SettlementUploadController.get_or_create_order_from_settlement_row(
                                row=row,
                                mapping=column_mapping,
                                platform_obj=platform_obj,
                                current_user=current_user,
                                variants_cache=variants_cache,
                                orders_cache=orders,
                                customer_cache=customer_cache
                            )

                        order = result["order"]
                        if result["product_created"]:
                            products_created += 1

                        if result["variant_created"]:
                            variants_created += 1

                        if result["customer_created"]:
                            customers_created += 1

                        if result["order_created"]:
                            orders_created += 1

                    # ✅ STATUS
                    # ✅ SAFE FIELD EXTRACTION
                    total_sale = clean_number(row.get(column_mapping.get("total_sale_amount")))
                    total_return = clean_number(row.get(column_mapping.get("total_return_amount")))
                    final_amt = clean_number(row.get(column_mapping.get("final_settlement_amount")))

                    commission_fee = clean_number(row.get(column_mapping.get("commission_fee")))
                    shipping_fee = clean_number(row.get(column_mapping.get("shipping_fee")))
                    return_shipping_charge = clean_number(row.get(column_mapping.get("return_shipping_charge")))
                    fixed_fee = clean_number(row.get(column_mapping.get("fixed_fee")))
                    warehousing_fee = clean_number(row.get(column_mapping.get("warehousing_fee")))

                    # ✅ CLAIMS
                    claims, compensation, recovery = extract_claim_data(row, column_mapping)
                    claim_amount = claims
                    # ✅ STATUS (ADD THIS BLOCK)
                    status_name = derive_order_status(row, column_mapping)
                    status_obj = status_cache.get(status_name)

                    # ✅ FLAGS
                    live_status_val = str(row.get(column_mapping.get("live_status"), "")).upper()
                    is_claim = claim_amount > 0
                    is_return = total_return < 0
                    is_rto = "RTO" in live_status_val

                    # ✅ FINAL AMOUNT
                    net_amount = final_amt + compensation + claims - recovery

                    # ✅ DATA
                    data = {
                        "platform": platform_obj,
                        "transaction_id": row.get(column_mapping.get("transaction_id")),

                        "payment_date": pd.to_datetime(
                            row.get(column_mapping.get("payment_date")),
                            errors="coerce"
                        ),

                        "total_sale_amount": total_sale,
                        "total_return_amount": total_return,
                        "final_settlement_amount": net_amount,

                        # 💰 DEDUCTIONS
                        "commission_fee": commission_fee,
                        "shipping_fee": shipping_fee,
                        "return_shipping_charge": return_shipping_charge,
                        "fixed_fee": fixed_fee,
                        "warehousing_fee": warehousing_fee,

                        # 🔁 RETURNS
                        "return_premium": clean_number(row.get(column_mapping.get("return_premium"))),
                        "return_premium_return": clean_number(row.get(column_mapping.get("return_premium_return"))),

                        # 🧾 CLAIMS
                        "claim_amount": claim_amount,

                        # 🚩 FLAGS
                        "is_claim": is_claim,
                        "is_return": is_return,
                        "is_rto": is_rto,

                        # TAX
                        "gst_percent": clean_number(row.get(column_mapping.get("gst_percent"))),

                        # EXTRA
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
                    orders_to_update = []
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

                        # 💰 deductions
                        "commission_fee",
                        "shipping_fee",
                        "return_shipping_charge",
                        "fixed_fee",
                        "warehousing_fee",

                        # 🔁 returns
                        "return_premium",
                        "return_premium_return",

                        # 🧾 claims (FIX)
                        "claim_amount",

                        # 🚩 flags (you were also missing these)
                        "is_claim",
                        "is_return",
                        "is_rto",

                        # tax + extra
                        "gst_percent",
                        "extra_data",
                    ],
                    batch_size=500
                ) 
                
            # ----------------------------------------- # RECALCULATE PROFITS # ----------------------------------------- 
            settlements = OrderSettlement.objects.filter( order__marketplace_sub_order_id__in=sub_orders ).select_related( "order", "order__variant", "order__product" ) 
            for settlement in settlements:
                ProfitCalculationService.calculate_order_profit( settlement.order, settlement )

            # return {
            #     "message": "Settlement uploaded successfully",
            #     "created": len(created),
            #     "updated": len(updated),
            #     "skipped": skipped,
            #     "skipped_details": skipped_details
            # }
            return {
                "success": True,
                "message": "Settlement uploaded successfully",

                "summary": {
                    "rows_processed": len(df),

                    "settlements_created": len(created),
                    "settlements_updated": len(updated),

                    "orders_created": orders_created,
                    "products_created": products_created,
                    "variants_created": variants_created,
                    "customers_created": customers_created,

                    "skipped": skipped
                },

                "skipped_details": skipped_details
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
    @staticmethod
    def get_or_create_order_from_settlement_row(
        row,mapping,platform_obj,
        current_user,
        variants_cache,
        orders_cache,
        customer_cache
    ):
        from datetime import date

        sub_order = normalize_sub_order(
            row[mapping["sub_order_id"]]
        )
        # -----------------------------
        # CREATION FLAGS
        # -----------------------------
        product_created = False
        variant_created = False
        customer_created = False
        order_created = False

        if sub_order in orders_cache:
            return {
                "order": orders_cache[sub_order],
                "product_created": False,
                "variant_created": False,
                "customer_created": False,
                "order_created": False,
            }

        # -----------------------------
        # PRODUCT DATA FROM SETTLEMENT
        # -----------------------------

        catalog_id = SettlementUploadController.normalize_catalog_id(
            row.get(mapping.get("catalog_id"))
        )

        quantity = int(
            clean_number(
                row.get(mapping.get("quantity"))
            ) or 1
        )

        selling_price = clean_number(
            row.get(mapping.get("listing_price"))
        )

        # -----------------------------
        # CUSTOMER
        # -----------------------------
        customer = customer_cache.get("settlement_customer")
        if not customer:
            customer = Customer.objects.create(
                name="Settlement Customer",
                email=f"settlement_{uuid.uuid4().hex[:8]}@local.com",
                phone=f"99999{uuid.uuid4().int % 100000}",
                address="Auto Created",
                state="Unknown",
                pincode="000000",
                created_by=current_user,
                updated_by=current_user
            )

            customer_cache["settlement_customer"] = customer
            customer_created = True

        # -----------------------------
        # PRODUCT
        # -----------------------------
        sku = str(
                row.get(mapping.get("sku"), "")
            ).strip().upper()
        variant = ProductVariant.objects.select_related(
                "product"
            ).filter(
                sku__iexact=sku
            ).first()

        product = variant.product if variant else None

        product_name = str(
                row.get(mapping.get("product_name"), "")
            ).strip()

        if not product:

            if not product:

                category = Category.objects.first()

                product = Product.objects.create(
                    catalog_id=catalog_id or str(uuid.uuid4().int)[:9],
                    name=product_name or sku,
                    category=category,
                    platform=platform_obj,
                    owner=current_user,
                    created_by=current_user,
                    updated_by=current_user,
                    is_auto_created=True,
                    requires_manual_review=True
                )
                product_created = True

        # -----------------------------
        # VARIANT
        # -----------------------------
        variant = variants_cache.get(sku.upper())

        if not variant:
            variant = ProductVariant.objects.select_related(
                "product"
            ).filter(
                sku__iexact=sku
            ).first()

            if variant:
                variants_cache[sku.upper()] = variant

        if not variant:

            variant = ProductVariant.objects.create(
            product=product,
            sku=sku,
            size="DEFAULT",
            color="DEFAULT",
            cost_price=0,
            selling_price=selling_price or 0,
            stock=9999,
            shipping_cost=0,
            rto_cost=0,
            is_auto_created=True,
            requires_manual_review=True
        )
            variant_created = True


        variants_cache[sku.upper()] = variant

        # -----------------------------
        # MARKETPLACE ORDER
        # -----------------------------
        # -----------------------------
        # ORDER DATE
        # -----------------------------
        order_date = None

        for field in ["order_date", "dispatch_date", "payment_date"]:

            col = mapping.get(field)

            if not col:
                continue

            dt = pd.to_datetime(
                row.get(col),
                errors="coerce"
            )

            if pd.notna(dt):
                order_date = dt.date()
                break

        if not order_date:
            order_date = timezone.now().date()
        marketplace_order, _ = MarketplaceOrder.objects.get_or_create(
            platform=platform_obj,
            marketplace_order_id=sub_order,
            defaults={
                "customer": customer,
                "order_date": order_date,
                "created_by": current_user,
                "updated_by": current_user
            }
        )
        # -----------------------------
        # UPDATE ORDER DATE IF CHANGED
        # -----------------------------
        if marketplace_order.order_date != order_date:
            marketplace_order.order_date = order_date
            marketplace_order.updated_by = current_user

            marketplace_order.save(
                update_fields=[
                    "order_date",
                    "updated_by",
                    "updated_at"
                ]
            )

        # -----------------------------
        # STATUS
        # -----------------------------
        status = OrderStatus.objects.filter(
            code="PLACED"
        ).first()

        if not status:
            status = OrderStatus.objects.first()

        # -----------------------------
        # ORDER
        # -----------------------------
        order_created = True

        order = Order.objects.create(
            marketplace_order=marketplace_order,
            marketplace_sub_order_id=sub_order,
            product=product,
            variant=variant,
            quantity=quantity,
            selling_price=selling_price,
            cost_price_at_order=variant.cost_price or 0,
            status=status,
            payment_type="PREPAID",
            created_by=current_user,
            updated_by=current_user
        )

        orders_cache[sub_order] = order

        return {
            "order": order,
            "product_created": product_created,
            "variant_created": variant_created,
            "customer_created": customer_created,
            "order_created": order_created,
        }
    @staticmethod
    def normalize_catalog_id(val):
        if pd.isna(val):
            return ""

        val = str(val).strip()

        if val.endswith(".0"):
            val = val[:-2]

        return val