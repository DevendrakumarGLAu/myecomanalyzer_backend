import pdfplumber
import re
from datetime import datetime

from customers.models import Customer
from platforms.models import Platform
from marketplace.models import MarketplaceOrder
from orders.models import Order, OrderStatus
from products.models import Product, ProductVariant


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

        name_match = re.search(r'BILL TO / SHIP TO\s*(.*?)\s*-', text)
        customer_name = name_match.group(1).strip() if name_match else "Unknown"

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
        # print(text)
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
            code="PLACED",
            defaults={
                "label": "Placed",
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
                            sku=data["sku"],
                            size=data.get("size"),
                            color=data.get("color")
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
                        quantity=data["quantity"],
                        selling_price=data["selling_price"],
                        status=status,
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