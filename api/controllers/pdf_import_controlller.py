import pdfplumber
import re
from datetime import datetime

from customers.models import Customer
from logistics.models import DeliveryPartner
from platforms.models import Platform
from marketplace.models import MarketplaceOrder
from orders.models import Order, OrderStatus
from products.models import Product, ProductVariant
from django.db.models import Q
from django.utils.dateparse import parse_date

from io import StringIO
import csv
from datetime import datetime
from django.db import transaction
from orders.models import OrderStatus

# Optional: mapping CSV status values to internal codes
STATUS_MAPPING = {
    "DELIVERED": "DELIVERED",
    "CANCELLED": "CANCELLED",
    "RTO_LOCKED": "RTO_COMPLETE",
    "RTO_COMPLETE": "RTO_COMPLETE",
    "PLACED": "PLACED",
    "LOST": "LOST",
    "SHIPPED": "SHIPPED",
    "READY_TO_SHIP": "READY_TO_SHIP",
    "DOOR_STEP_EXCHANGED": "DOOR_STEP_EXCHANGED",
    # optional
    "PLACED": "READY_TO_SHIP",
    
}
class InvoiceExtractController:
    

   # --------------------------------------------------
    # 2. PARSE PAGE TEXT
    # --------------------------------------------------
    @staticmethod
    def parse_invoice_data(text):
        if not text:
            raise ValueError("Empty PDF page text")

        sub_order_match = re.search(r'(\d+_\d+)', text)
        if not sub_order_match:
            raise ValueError("Sub-order ID not found")

        marketplace_sub_order_id = sub_order_match.group(1)
        marketplace_order_id = marketplace_sub_order_id

        amount_match = re.search(r'Total\s+Rs\.0\.00\s+Rs\.(\d+\.\d+)', text)
        selling_price = float(amount_match.group(1)) if amount_match else 0.0

        # name_match = re.search(r'BILL TO / SHIP TO\s*(.*?)\s*-', text)
        # customer_name = name_match.group(1).strip() if name_match else "Unknown"
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        customer_name = "Unknown"
        for i, line in enumerate(lines):
            if "BILL TO / SHIP TO" in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if "-" in next_line:
                        customer_name = next_line.split("-")[0].strip()
                    else:
                        customer_name = next_line.strip()
                break
        pincode_match = re.search(r'(\d{6})', text)
        pincode = pincode_match.group(1) if pincode_match else "000000"

        state_match = re.search(r',\s*([A-Za-z\s]+),\s*\d{6}', text)
        state = state_match.group(1).strip() if state_match else "Unknown"

        return {
            "marketplace_order_id": marketplace_order_id,
            "marketplace_sub_order_id": marketplace_sub_order_id,
            "selling_price": selling_price,
            "customer_name": customer_name,
            "state": state,
            "pincode": pincode,
            "address": text
        }
    
    @staticmethod
    def extract_product_from_text(text, marketplace_sub_order_id):
        if not text:
            raise ValueError("Empty page text")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        # print(lines)
        for line in lines:
            if marketplace_sub_order_id in line:
                # Example line:
                # 0O0-Z_wu 2.2 1 Pink 259318205301888448_1

                parts = line.split()

                if len(parts) < 5:
                    continue

                sku = parts[0]
                size = parts[1]
                quantity = int(parts[2]) if parts[2].isdigit() else 1
                color = parts[3]
                order_id = parts[4]

                return sku, size, quantity, color

        raise ValueError(
            f"Product row not found for order {marketplace_sub_order_id}"
        )
    
    # 1. EXTRACT ORDER DATE FROM TABLES
    # --------------------------------------------------
    
    @staticmethod
    def extract_order_date_from_text(text, marketplace_sub_order_id):
        print(text)
        if not isinstance(text, str):
            raise ValueError(
                f"Order Date text invalid for order {marketplace_sub_order_id}"
            )

        # Normalize line breaks
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            # Look for line containing marketplace order id
            if marketplace_sub_order_id.split("_")[0] in line:
                # Extract all dates from that line
                dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', line)

                if dates:
                    # First date = Order Date
                    return datetime.strptime(dates[0], "%d.%m.%Y").date()

        raise ValueError(
            f"Order Date not found for order {marketplace_sub_order_id}"
        )
    # --------------------------------------------------
    # 3. SAVE INVOICE TO DATABASE (PDF STAYS OPEN)
    # --------------------------------------------------
    @staticmethod
    def save_invoice_to_db(file_path, platform_code, current_user):
        import pandas as pd
        import os
        error_file_url = None
        # Validate platform early and return an explicit error if not found
        try:
            platform = Platform.objects.get(code=platform_code)
        except Platform.DoesNotExist:
            return {
                "success": False,
                "message": "Invoice processed with errors",
                "error": f"Platform matching query does not exist for code '{platform_code}'.",
                "data": None
            }
        status, _ = OrderStatus.objects.get_or_create(
            code="READY_TO_SHIP",
            defaults={
                "label": "Ready To Ship",
                "created_by": current_user,
                "updated_by": current_user
            }
        )

        imported_orders = []
        duplicate_orders = []
        error_orders = []

        with pdfplumber.open(file_path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""

                    data = InvoiceExtractController.parse_invoice_data(text)

                    # sku, quantity = InvoiceExtractController.extract_product_from_text(
                    #     text, data["marketplace_sub_order_id"]
                    # )
                    sku, size, quantity, color = InvoiceExtractController.extract_product_from_text(
                            text, data["marketplace_sub_order_id"]
                        )
                    delivery_partner_name = InvoiceExtractController.extract_delivery_partner(text)
                    payment_type = InvoiceExtractController.extract_payment_type(text)

                    data["delivery_partner"] = delivery_partner_name
                    data["payment_type"] = payment_type
                    data["sku"] = sku
                    data["size"] = size
                    data["color"] = color
                    data["quantity"] = quantity
                    try:
                        order_date = InvoiceExtractController.extract_order_date_from_text(
                            text, data["marketplace_sub_order_id"]
                        )
                    except Exception:
                        order_date = datetime.today().date()
                        
                    delivery_partner_obj = None
                    if delivery_partner_name:
                        delivery_partner_obj, _ = DeliveryPartner.objects.get_or_create(
                            name=delivery_partner_name,
                            defaults={"code": delivery_partner_name.upper().replace(" ", "_")}
                        )

                    # 🔁 DUPLICATE CHECK
                    if Order.objects.filter(
                        marketplace_sub_order_id=data["marketplace_sub_order_id"]
                    ).exists():
                        duplicate_orders.append({
                            "order_id": data["marketplace_sub_order_id"],
                            "reason": "Order already exists"
                        })
                        continue

                    # product = Product.objects.get(sku=data["sku"])
                    # variant = ProductVariant.objects.select_related("product").get(sku=data["sku"])
                    try:
                        variant = ProductVariant.objects.select_related("product").filter(
                            sku__iexact=sku,
    size=size,
    color__iexact=color
                        ).first()
                        
                        if not variant:   # ✅ ADD THIS CHECK
                            error_orders.append({
                                "order_id": data.get("marketplace_sub_order_id"),
                                "sku": data.get("sku"),
                                "size": data.get("size"),
                                "color": data.get("color"),
                                "reason": "Variant not found (size/color mismatch)"
                            })
                            continue
               

                    except Exception as e:
                        error_orders.append({
                            "order_id": data.get("marketplace_sub_order_id", f"page-{idx}"),
                            "sku": data.get("sku"),
                            "size": data.get("size"),
                            "color": data.get("color"),
                            "reason": str(e)   # ✅ always use "reason"
                        })

                    product = variant.product

                    customer, _ = Customer.objects.get_or_create(
                        name=data["customer_name"],
                        state=data["state"],
                        pincode=data["pincode"],
                        defaults={
                            "address": data["address"],
                            "created_by": current_user,
                            "updated_by": current_user
                        }
                    )

                    marketplace_order, _ = MarketplaceOrder.objects.get_or_create(
                        platform=platform,
                        marketplace_order_id=data["marketplace_order_id"],
                        defaults={
                            "customer": customer,
                            "order_date": order_date,
                            "created_by": current_user,
                            "updated_by": current_user
                        }
                    )

                    Order.objects.create(
                        marketplace_order=marketplace_order,
                        marketplace_sub_order_id=data["marketplace_sub_order_id"],
                        product=product,
                        variant=variant,
                        quantity=data["quantity"],
                        selling_price=data["selling_price"],
                        status=status,
                        delivery_partner=delivery_partner_obj,
                        payment_type=data.get("payment_type", "COD"),
                        created_by=current_user,
                        updated_by=current_user
                    )

                    imported_orders.append(data["marketplace_sub_order_id"])

                except ProductVariant.DoesNotExist:
                    error_orders.append({
                        "order_id": data.get("marketplace_sub_order_id"),
                        "sku": data.get("sku"),
                        "size": data.get("size"),
                        "color": data.get("color"),
                        "reason": str(e)   # ✅ changed key from "error" → "reason"
                    })

                except Exception as e:
                    error_orders.append({
                        "order_id": data.get("marketplace_sub_order_id", f"page-{idx}"),
                        "sku": data.get("sku"),
                        "size": data.get("size"),
                        "color": data.get("color"),
                        "reason": str(e)
                    })
                    
        if error_orders:
            formatted_errors = []

            for err in error_orders:
                formatted_errors.append({
                    "Order ID": err.get("order_id", ""),
                    "SKU": err.get("sku", ""),
                    "Size": err.get("size", ""),
                    "Color": err.get("color", ""),
                    "Error Reason": err.get("reason") or err.get("error", "")
                })
            df = pd.DataFrame(formatted_errors)
            df = df.sort_values(by="Order ID")
            # ✅ SAVE FILE
            file_name = f"error_report.xlsx"
            file_path = os.path.join("media", file_name)

            df.to_excel(file_path, index=False)

            error_file_url = "/media/" + file_name

        return {
            "summary": {
                "total": len(pdf.pages),
                "imported": len(imported_orders),
                "duplicates": len(duplicate_orders),
                "errors": len(error_orders),
                "not_inserted": len(duplicate_orders) + len(error_orders)
            },
            "imported_orders": imported_orders,
            "duplicate_orders": duplicate_orders,
            "error_orders": error_orders,
            "error_file": error_file_url
        }
        
    def process_meesho_invoice(current_user,platform_code,page,limit,search,status,state,sku,start_date,end_date,sort_by,order):
        try:
            """
            Get order dispatch data with:
            - Product name
            - SKU
            - Variant (size, color)
            - Settlement amount
            - Customer-end status"""
            # import pdb
            # pdb.set_trace()
            # 1️⃣ Base queryset: Orders for given platform
            queryset = Order.objects.select_related(
                    "product",
                    "variant",
                    "status",
                    "marketplace_order",
                    "marketplace_order__platform",
                ).prefetch_related("settlements").filter(
                    marketplace_order__platform__code__iexact=platform_code,
                    created_by=current_user   # 👈 KEY FILTER
                )

            # 2️⃣ Dynamic filters
            if search:
                queryset = queryset.filter(
                    Q(marketplace_sub_order_id__icontains=search) |
                    Q(product__name__icontains=search) |
                    Q(variant__sku__icontains=search) |
                    Q(status__label__icontains=search)
                )

            if status:
                queryset = queryset.filter(status__code=status)

            if state:
                queryset = queryset.filter(marketplace_order__state__iexact=state)

            if sku:
                queryset = queryset.filter(variant__sku__iexact=sku)

            if start_date:
                start = parse_date(start_date)
                if start:
                    queryset = queryset.filter(created_at__date__gte=start)

            if end_date:
                end = parse_date(end_date)
                if end:
                    queryset = queryset.filter(created_at__date__lte=end)

            # 3️⃣ Sorting
            if sort_by:
                if order.lower() == 'desc':
                    sort_by = f'-{sort_by}'
                queryset = queryset.order_by(sort_by)

            # 4️⃣ Pagination
            total_orders = queryset.count()
            start_index = (page - 1) * limit
            end_index = start_index + limit
            orders = queryset[start_index:end_index]

            # 5️⃣ Prepare response
            data = []
            for o in orders:
                settlement = o.settlements.order_by('-payment_date').first()
                data.append({
                    "order_id": o.marketplace_order.marketplace_order_id,
                    "sub_order_id": o.marketplace_sub_order_id,
                    "product_name": o.product.name,
                    "sku": o.variant.sku if o.variant else None,
                    "size": o.variant.size if o.variant else None,
                    "color": o.variant.color if o.variant else None,
                    "settlement_amount": float(settlement.final_settlement_amount) if settlement else 0,
                    "status": o.status.label,
                    "status_code": o.status.code,
                    "order_date": o.marketplace_order.order_date if o.marketplace_order else None
                })

            # 6️⃣ Return response
            return {
                "page": page,
                "total_orders": total_orders,
                "orders": data
            }

        except Exception as e:
            print(f"Error in process_meesho_invoice: {str(e)}")
            return {
                "status": "error",
                "message": "An error occurred while processing Meesho invoices",
                "error": str(e),
            }
    @staticmethod
    def update_order_status_from_csv(file, current_user):
        content = file.read().decode("utf-8")
        reader = csv.DictReader(StringIO(content))

        updated = []
        errors = []
        not_found = []

        with transaction.atomic():
            for idx, row in enumerate(reader, start=1):
                try:
                    sub_order_id = row.get("Sub Order No")
                    raw_status = row.get("Reason for Credit Entry")

                    if not sub_order_id or not raw_status:
                        errors.append({
                            "row": idx,
                            "reason": "Missing Sub Order No or Status"
                        })
                        continue

                    # Map status
                    status_code = STATUS_MAPPING.get(
                        raw_status.strip(), raw_status.strip()
                    )

                    status_label = status_code.replace("_", " ").title()

                    # Get/Create status
                    status_obj, _ = OrderStatus.objects.get_or_create(
                        code=status_code,
                        defaults={
                            "label": status_label,
                            "created_by": current_user,
                            "updated_by": current_user
                        }
                    )

                    # Find order
                    order = Order.objects.filter(
                        marketplace_sub_order_id=sub_order_id
                    ).first()

                    if not order:
                        not_found.append({
                            "sub_order_id": sub_order_id,
                            "reason": "Order not found"
                        })
                        continue

                    # Update status
                    order.status = status_obj
                    order.updated_by = current_user
                    order.save()

                    updated.append({
                        "sub_order_id": sub_order_id,
                        "status": status_code
                    })

                except Exception as e:
                    errors.append({
                        "row": idx,
                        "sub_order_id": row.get("Sub Order No"),
                        "reason": str(e)
                    })

        return {
            "summary": {
                "total": len(updated) + len(errors) + len(not_found),
                "updated": len(updated),
                "errors": len(errors),
                "not_found": len(not_found)
            },
            "updated_orders": updated,
            "errors": errors,
            "not_found": not_found
        }
    @staticmethod
    def extract_delivery_partner(text):
        if not text:
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        known_partners = [
            "Shadowfax",
            "Xpressbees",
            "Delhivery",
            "Ecom Express",
            "Ekart",
            "Blue Dart",
            "Meesho"
        ]

        for line in lines:
            for partner in known_partners:
                if partner.lower() in line.lower():
                    return partner

        return None
    
    @staticmethod
    def extract_payment_type(text):
        if not text:
            return "PREPAID"

        text_upper = text.upper()

        if "COD" in text_upper:
            return "COD"
        if "PREPAID" in text_upper:
            return "PREPAID"

        return "PREPAID"