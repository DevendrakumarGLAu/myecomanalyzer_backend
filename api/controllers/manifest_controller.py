from collections import defaultdict
from datetime import datetime

from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from orders.models import Order


class ManifestController:

    @staticmethod
    def get_manifest(
        current_user,
        manifest_date=None,
        platform_code="MEESHO",
        search=None,
        page=1,
        limit=100,
    ):

        # -----------------------------
        # Parse date
        # -----------------------------
        if manifest_date:
            parsed = parse_date(manifest_date)

            if parsed is None:
                try:
                    parsed = datetime.strptime(
                        manifest_date,
                        "%d-%m-%Y"
                    ).date()
                except ValueError:
                    parsed = timezone.localdate()

            manifest_date = parsed
        else:
            manifest_date = timezone.localdate()

        # -----------------------------
        # Base Query
        # -----------------------------
        queryset = (
            Order.objects.select_related(
                "variant",
                "product",
                "delivery_partner",
                "marketplace_order",
                "marketplace_order__platform",
            )
            .filter(
                created_by=current_user,
                status__code="READY_TO_SHIP",
                marketplace_order__platform__code__iexact=platform_code,

                # ✅ PDF Upload Date (Order Created Date)
                created_at__date=manifest_date,
            )
        )

        # -----------------------------
        # Search
        # -----------------------------
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search)
                | Q(variant__sku__icontains=search)
                | Q(variant__size__icontains=search)
                | Q(variant__color__icontains=search)
                | Q(delivery_partner__name__icontains=search)
            )

        queryset = (
            queryset.values(
                "delivery_partner__name",
                "product__name",
                "variant__sku",
                "variant__size",
                "variant__color",
            )
            .annotate(
                quantity=Sum("quantity")
            )
            .order_by(
                "delivery_partner__name",
                "product__name",
                "variant__sku",
                "variant__size",
            )
        )

        total_records = queryset.count()

        # -----------------------------
        # Pagination
        # -----------------------------
        start = (page - 1) * limit
        end = start + limit

        queryset = queryset[start:end]

        partner_map = defaultdict(list)

        total_quantity = 0

        for item in queryset:

            partner = item["delivery_partner__name"] or "Unknown"

            partner_map[partner].append({
                "product_name": item["product__name"],
                "sku": item["variant__sku"],
                "size": item["variant__size"],
                "color": item["variant__color"],
                "quantity": item["quantity"],
            })

            total_quantity += item["quantity"]

        response = []

        for partner, products in partner_map.items():

            response.append({
                "delivery_partner": partner,
                "total_products": len(products),
                "total_quantity": sum(p["quantity"] for p in products),
                "items": products,
            })

        return {
            "manifest_date": manifest_date.strftime("%Y-%m-%d"),
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "delivery_partner_count": len(response),
            "total_quantity": total_quantity,
            "data": response,
        }