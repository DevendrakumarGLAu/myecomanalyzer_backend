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
        marketplace_order_id = marketplace_sub_order_id.split("_")[0]

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
        print(text)
        if not text:
            raise ValueError("Empty page text")

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if marketplace_sub_order_id in line:
                # Example line:
                # 0O0-Z_wu 2.2 1 Pink 259318205301888448_1

                parts = line.split()

                if len(parts) < 2:
                    continue

                sku = parts[0]

                quantity = 1
                for value in parts[1:]:
                    if value.isdigit():
                        quantity = int(value)
                        break

                return sku, quantity

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

                    sku, quantity = InvoiceExtractController.extract_product_from_text(
                        text, data["marketplace_sub_order_id"]
                    )

                    data["sku"] = sku
                    data["quantity"] = quantity

                    order_date = InvoiceExtractController.extract_order_date_from_text(
                        text, data["marketplace_sub_order_id"]
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
                    variant = ProductVariant.objects.select_related("product").get(sku=data["sku"])

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
                        "order_id": data.get("marketplace_sub_order_id", f"page-{idx}"),
                        "error": "SKU not found"
                    })

                except Exception as e:
                    error_orders.append({
                        "order_id": data.get("marketplace_sub_order_id", f"page-{idx}"),
                        "error": str(e)
                    })

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
            "error_orders": error_orders
        }