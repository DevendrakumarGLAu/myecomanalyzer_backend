from typing import Optional
from django.contrib.auth.models import User
from api.controllers.pagination_controller import Pagination
from customers.models import Customer
from marketplace.models import MarketplaceOrder
from orders.models import Order
from payments.models import OrderSettlement
from platforms.models import Platform
from products.models import Product, ProductVariant, CostPriceUpdateHistory
from fastapi import HTTPException
from api.schemas.product_schema import ProductRequest, ProductResponse, ProductUpdateRequest, ProductVariantResponse
from django.db.models import Q
from django.db import transaction
import os

class ProductController:

    @staticmethod
    def _serialize_product(product):
        """
        Builds a ProductResponse from a Product instance whose
        variants/category/platform are already loaded (via select_related +
        prefetch_related, or already in-memory) — never re-queries.
        """
        variants = list(product.variants.all())
        first_variant = variants[0] if variants else None

        return ProductResponse(
            id=product.id,
            catalog_id=product.catalog_id,
            name=product.name,
            image=ProductController.get_image_url(product.image) if product.image else None,
            category_id=product.category_id,
            category_name=product.category.name if product.category else "",
            platform_code=product.platform.code if product.platform else None,
            sku=first_variant.sku if first_variant else None,
            color=first_variant.color if first_variant else None,
            cost_price=first_variant.cost_price if first_variant else None,
            selling_price=first_variant.selling_price if first_variant else None,
            stock=first_variant.stock if first_variant else None,
            gst_percent=float(product.gst_percent),
            commission_percent=float(product.commission_percent),
            is_active=product.is_active,
            variants=[ProductVariantResponse.model_validate(v) for v in variants],
        )

    @staticmethod
    def get_product_by_id(product_id: int, current_user: User):
        """
        Fetch single product for current user (active or inactive).
        Return None if not found.

        No is_active filter here — this is also used by
        toggle_product_active_logic to flip an inactive product back to
        active, which would always 404 if this only matched active ones.
        Ownership (owner=current_user) is the real security boundary, not
        active status.
        """
        product = Product.objects.filter(
            id=product_id,
            owner=current_user,
        ).select_related("category", "platform").prefetch_related("variants").first()

        if not product:
            return None
        return product

    @staticmethod
    def get_product_response_by_id(product_id: int, current_user: User):
        """
        Serialized version of get_product_by_id, for the GET /get/{id}
        endpoint. get_product_by_id itself must keep returning the raw model
        (delete_product_logic/toggle_product_active_logic call .save()/
        .soft_delete() on it), but the route's response_model is
        ProductResponse, which needs sku/color/cost_price/etc. derived from
        the first variant plus category_name/platform_code from the FKs —
        fields that don't exist on the raw Product model, so returning it
        directly there fails Pydantic validation on every request.
        """
        product = ProductController.get_product_by_id(product_id, current_user)
        if not product:
            return None
        return ProductController._serialize_product(product)

    @staticmethod
    def get_all_products(
        current_user: User,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        platform: Optional[int] = None,
        status: str = "all",
    ):
        try:
            # status feeds the Active/Paused tabs on the admin table — each
            # tab requests its own filtered, paginated list rather than
            # splitting one mixed page client-side.
            filters = {
                "owner": current_user,
            }
            if status == "active":
                filters["is_active"] = True
            elif status == "paused":
                filters["is_active"] = False
            if platform:
                filters["platform__code"] = platform
            query = (
                Product.objects
                .filter(**filters)
                .select_related("category", "platform")
                .prefetch_related("variants")
                .only(
                    "id",
                    "catalog_id",
                    "name",
                    "image",
                    "category_id",
                    "platform_id",
                    "gst_percent",
                    "commission_percent",
                    "is_active",
                    "platform__code",
                    # category__name is accessed below (p.category.name) —
                    # without it in .only(), it's a deferred field that Django
                    # lazy-loads with its own query on first access, one more
                    # per-product query hiding behind select_related("category").
                    "category__name",
                )
                .order_by("-id")
            )

            if search:
                variant_product_ids = ProductVariant.objects.filter(
                    sku__icontains=search
                ).values_list("product_id", flat=True)

                query = query.filter(
                    Q(name__icontains=search)
                    | Q(catalog_id__icontains=search)
                    | Q(category__name__icontains=search)
                    | Q(id__in=variant_product_ids)
                )

            page_data = Pagination.paginate(query, page, limit)

            products = page_data["queryset"]
            meta = page_data["meta"]

            items = []
            for p in products:
                # p.variants.all() reuses the prefetch_related("variants")
                # cache above — zero extra queries. Calling .exists()/.first()
                # on the manager instead (as this used to) bypasses that
                # cache and issues a fresh query every time, so this loop was
                # doing up to 10 extra round-trips per product (5 fields x
                # both .exists() and .first()) despite prefetch_related
                # already having every variant in memory.
                variants = list(p.variants.all())
                first_variant = variants[0] if variants else None
                category_name = p.category.name if p.category else None

                items.append(
                    ProductResponse(
                        id=p.id,
                        catalog_id=p.catalog_id,
                        name=p.name,
                        image=ProductController.get_image_url(p.image) if p.image else None,
                        category_id=p.category_id,
                        category_name=category_name,
                        sku=first_variant.sku if first_variant else None,
                        color=first_variant.color if first_variant else None,
                        cost_price=first_variant.cost_price if first_variant else None,
                        selling_price=first_variant.selling_price if first_variant else None,
                        stock=first_variant.stock if first_variant else None,
                        platform_code=p.platform.code if p.platform else None,
                        gst_percent=float(p.gst_percent),
                        commission_percent=float(p.commission_percent),
                        is_active=p.is_active,
                        variants=[
                            ProductVariantResponse.model_validate(v)
                            for v in variants
                        ]
                    )
                )

            return {
                "items": items,
                **meta
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching products: {str(e)}"
            )


    @staticmethod
    def add_product(payload: ProductRequest, current_user):
        try:
            with transaction.atomic():

                # Get platform
                platform_obj = None
                if payload.platform_code:
                    platform_obj = Platform.objects.filter(
                        code=payload.platform_code
                    ).first()

                # Create product
                product = Product.objects.create(
                    catalog_id=payload.catalog_id,
                    name=payload.name,
                    image=payload.image,
                    category_id=payload.category_id,
                    platform=platform_obj,
                    owner=current_user,
                    created_by=current_user,
                    updated_by=current_user,
                    gst_percent=payload.gst_percent,
                    commission_percent=payload.commission_percent,
                    is_active=payload.is_active
                )

                # Create variants
                variants = [
                    ProductVariant(
                        product=product,
                        sku=v.sku,
                        size=v.size,
                        color=v.color,
                        cost_price=v.cost_price,
                        selling_price=v.selling_price,
                        stock=v.stock,
                        shipping_cost=v.shipping_cost or 0.0,
                        rto_cost=v.rto_cost or 0.0
                    )
                    for v in payload.variants
                ]

                ProductVariant.objects.bulk_create(variants)

                return ProductController.build_product_response(product)

        except Exception as e:
            import traceback
            print(traceback.format_exc())

            raise HTTPException(
                status_code=500,
                detail=f"Error while creating product: {str(e)}"
            )


    # @staticmethod
    # def update_product_logic(product_id: int, payload: ProductUpdateRequest, current_user: User):
    #     """
    #     Update product and its variants. Variants are replaced if provided.
    #     """
    #     try:
    #         product = ProductController.get_product_by_id(product_id, current_user)
    #         if not product:
    #             raise HTTPException(status_code=404, detail="Product not found")

    #         update_data = payload.dict(exclude_unset=True)
           

    #         # --- Update Product fields ---
    #         for field, value in update_data.items():
    #             if field != "variants":
    #                 if field == "marketplace":
    #                     setattr(product, "platform_id", value)
    #                 else:
    #                     setattr(product, field, value)

            
    #         if "platform_code" in update_data:
    #             platform_obj = Platform.objects.filter(code=update_data["platform_code"]).first()
    #             product.platform = platform_obj
    #         product.updated_by = current_user
    #         product.is_auto_created = False
    #         product.requires_manual_review = False
    #         product.save()

    #         # --- Update Variants if provided ---
    #         if "variants" in update_data:
                
    #             existing_variants = {v.id: v for v in product.variants.all()}
    #             incoming_variants = payload.variants or []
    #             incoming_ids = []
    #             for variant_data in incoming_variants:
    #                 variant_id = variant_data.id

    #                 if variant_id and variant_id in existing_variants:
    #                     # Update existing variant
    #                     variant = existing_variants[variant_id]
    #                     old_cost_price = variant.cost_price
    #                     variant.sku = variant_data.sku
    #                     variant.size = variant_data.size
    #                     variant.color = variant_data.color
    #                     variant.cost_price = variant_data.cost_price
    #                     variant.selling_price = variant_data.selling_price
    #                     variant.stock = variant_data.stock
    #                     variant.shipping_cost = variant_data.shipping_cost or 0.0
    #                     variant.rto_cost = variant_data.rto_cost or 0.0
    #                     if old_cost_price != variant_data.cost_price:
    #                         CostPriceUpdateHistory.objects.create(
    #                             variant=variant,
    #                             old_cost_price=old_cost_price,
    #                             new_cost_price=variant_data.cost_price,
    #                             updated_by=current_user
    #                         )
    #                     variant.is_auto_created = False
    #                     variant.requires_manual_review = False
    #                     variant.save()
    #                     incoming_ids.append(variant_id)
    #                 else:
    #                     ProductVariant.objects.update_or_create(
    #                         product=product,
    #                         sku=variant_data.sku,
    #                         size=variant_data.size,
    #                         color=variant_data.color,
    #                         defaults={
    #                             "cost_price": variant_data.cost_price,
    #                             "selling_price": variant_data.selling_price,
    #                             "stock": variant_data.stock,
    #                             "shipping_cost": variant_data.shipping_cost or 0,
    #                             "rto_cost": variant_data.rto_cost or 0,
    #                             "is_auto_created": False,
    #                             "requires_manual_review": False,
    #                         }
    #                     )

    #         # Prefetch variants for response
    #         product = Product.objects.prefetch_related("variants").get(id=product.id)
    #         sku = product.variants.first().sku if product.variants.exists() else None
    #         category_name = product.category.name if product.category else None
    #         color= product.variants.first().color if product.variants.exists() else None
    #         cost_price = product.variants.first().cost_price if product.variants.exists() else None
    #         selling_price = product.variants.first().selling_price if product.variants.exists() else None
    #         stock = product.variants.first().stock if product.variants.exists() else None
    #         catalog_id = product.catalog_id if product.catalog_id else None
    #         platform_code = product.platform.code if product.platform else None
    #         # Convert to Pydantic schema
    #         product_response = ProductResponse(
    #                 id=product.id,
    #                 catalog_id=product.catalog_id,
    #                 name=product.name,
    #                 category_id=product.category_id,
    #                 category_name=category_name,  # ✅ ADD THIS
    #                 platform_code=product.platform.code if product.platform else None,  # ✅ also fix this
    #                 gst_percent=float(product.gst_percent),
    #                 commission_percent=float(product.commission_percent),
    #                 sku=sku,
    #                 color=color,
    #                 cost_price=cost_price,
    #                 selling_price=selling_price,
    #                 stock=stock,
    #                 is_active=product.is_active,
    #                 variants=[
    #                     ProductVariantResponse.model_validate(v)
    #                     for v in product.variants.all()
    #                 ]
    #             )
    #         return product_response

    #     except Exception as e:
    #         raise HTTPException(
    #             status_code=500,
    #             detail=f"Error while updating product: {str(e)}"
    #         )
    @staticmethod
    def update_product_logic(
        product_id: int,
        payload: ProductUpdateRequest,
        current_user: User,
    ):

        # category/platform are plain ForeignKeys — select_related joins them
        # in the same query (0 extra round-trips). variants is the reverse
        # side of a FK, which is what prefetch_related is actually for; the
        # old code used prefetch_related for all three, which for category/
        # platform means 2 extra queries instead of 0.
        product = Product.objects.select_related(
            "category",
            "platform",
        ).prefetch_related(
            "variants",
        ).filter(
            id=product_id,
            owner=current_user
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # -----------------------
        # Update Product
        # -----------------------
        if payload.image is not None:
            product.image = payload.image
            
        if payload.catalog_id is not None:
            product.catalog_id = payload.catalog_id

        if payload.name is not None:
            product.name = payload.name

        if payload.category_id is not None:
            product.category_id = payload.category_id

        if payload.gst_percent is not None:
            product.gst_percent = payload.gst_percent

        if payload.commission_percent is not None:
            product.commission_percent = payload.commission_percent

        if payload.is_active is not None:
            product.is_active = payload.is_active

        if payload.platform_code:
            platform = Platform.objects.filter(
                code=payload.platform_code
            ).first()

            if platform:
                product.platform = platform

        product.updated_by = current_user
        product.is_auto_created = False
        product.requires_manual_review = False
        product.save()

        # -----------------------
        # Update Variants
        # -----------------------

        if payload.variants:

            # product.variants.all() reuses the prefetch_related("variants")
            # cache from the fetch above — one query for every variant this
            # product has, instead of the loop below previously running a
            # separate filter().first() PLUS a separate duplicate-check
            # .exists() query for every single item in the payload (2+
            # queries x N variants, on top of a create() per changed cost and
            # a save() per item).
            existing_variants = list(product.variants.all())
            variants_by_id = {v.id: v for v in existing_variants}
            variants_by_key = {}
            for v in existing_variants:
                variants_by_key.setdefault((v.sku, v.size, v.color), []).append(v)

            processed_ids = []
            variants_to_save = []
            new_variants = []
            cost_history_entries = []

            for item in payload.variants:

                sku = item.sku.strip().upper()
                size = item.size.strip() if item.size else None
                color = item.color.strip().upper() if item.color else None

                # ---------- Existing Variant ----------
                if item.id:

                    variant = variants_by_id.get(item.id)

                    if not variant:
                        continue

                    duplicate = any(
                        v.id != variant.id
                        for v in variants_by_key.get((sku, size, color), [])
                    )

                    if duplicate:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Duplicate variant ({sku}, {size}, {color})"
                        )

                    old_cost = variant.cost_price or 0
                    # Save history BEFORE updating the variant
                    if variant.cost_price != item.cost_price:
                        cost_history_entries.append(CostPriceUpdateHistory(
                            variant=variant,
                            old_cost_price=old_cost,
                            new_cost_price=item.cost_price,
                            effective_from=item.effective_from,
                            created_by=current_user,
                            updated_by=current_user,
                        ))

                    variant.sku = sku
                    variant.size = size
                    variant.color = color
                    variant.cost_price = item.cost_price
                    variant.cost_price_pending = False
                    variant.selling_price = item.selling_price
                    variant.stock = item.stock
                    variant.shipping_cost = item.shipping_cost or 0
                    variant.rto_cost = item.rto_cost or 0
                    variant.is_auto_created = False
                    variant.requires_manual_review = False

                    variants_to_save.append(variant)
                    processed_ids.append(variant.id)

                # ---------- New Variant ----------
                else:

                    # A "new" item that actually collides with an existing
                    # (product, sku, size, color) — treat as an update
                    # instead of a separate get_or_create() round-trip.
                    existing_match = variants_by_key.get((sku, size, color))

                    if existing_match:
                        variant = existing_match[0]
                        variant.cost_price = item.cost_price
                        variant.selling_price = item.selling_price
                        variant.stock = item.stock
                        variant.shipping_cost = item.shipping_cost or 0
                        variant.rto_cost = item.rto_cost or 0
                        variants_to_save.append(variant)
                        processed_ids.append(variant.id)
                    else:
                        new_variants.append(ProductVariant(
                            product=product,
                            sku=sku,
                            size=size,
                            color=color,
                            cost_price=item.cost_price,
                            selling_price=item.selling_price,
                            stock=item.stock,
                            shipping_cost=item.shipping_cost or 0,
                            rto_cost=item.rto_cost or 0,
                            is_auto_created=False,
                            requires_manual_review=False,
                        ))

            for variant in variants_to_save:
                variant.save()

            if cost_history_entries:
                CostPriceUpdateHistory.objects.bulk_create(cost_history_entries)

            if new_variants:
                created = ProductVariant.objects.bulk_create(new_variants)
                processed_ids.extend(v.id for v in created)

            # Optional: delete removed variants
            ProductVariant.objects.filter(
                    product=product
                ).exclude(
                    id__in=processed_ids
                ).update(is_active=False)

        product.refresh_from_db()
        return ProductController._serialize_product(product)

    @staticmethod
    def delete_product_logic(product_id: int, current_user: User):
        """
        Soft delete product for current user
        """
        product = ProductController.get_product_by_id(product_id, current_user)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product.soft_delete(user=current_user)  # uses BaseModel soft_delete
        return {"status": "success", "deleted_at": product.deleted_at}

    @staticmethod
    def toggle_product_active_logic(product_id: int, current_user: User):
        """
        Toggle active/inactive status of a product
        """
        product = ProductController.get_product_by_id(product_id, current_user)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product.is_active = not product.is_active
        product.updated_by = current_user
        product.save()

        # response_model=ProductResponse on the route needs sku/color/
        # category_name/etc. that don't exist on the raw Product model —
        # returning it directly (as this used to) fails Pydantic validation
        # on every call.
        return ProductController._serialize_product(product)

    @staticmethod
    def build_product_response(product):
        product = Product.objects.select_related(
            "category", "platform"
        ).prefetch_related(
            "variants"
        ).get(id=product.id)

        return ProductController._serialize_product(product)
        
    @staticmethod
    def delete_product(product_id: int, current_user: User):
        # Ownership check — this is a hard/permanent delete (unlike
        # delete_product_logic's soft delete above), so it must never operate
        # on another tenant's product.
        owned = Product.objects.filter(id=product_id, owner=current_user).exists()
        if not owned:
            raise HTTPException(status_code=404, detail="Product not found")

        with transaction.atomic():
            # Capture which marketplace orders / customers this product's
            # orders touch BEFORE deleting them, so the orphan cleanup below
            # can check only those specific rows — the previous version ran
            # an unscoped, system-wide scan of every MarketplaceOrder and
            # every Customer on EVERY single product delete, regardless of
            # which seller or product was involved.
            affected_marketplace_order_ids = list(
                Order.objects.filter(product_id=product_id)
                .values_list("marketplace_order_id", flat=True).distinct()
            )
            affected_customer_ids = list(
                MarketplaceOrder.objects.filter(id__in=affected_marketplace_order_ids)
                .values_list("customer_id", flat=True).distinct()
            )

            OrderSettlement.objects.filter(
                order__product_id=product_id
            ).delete()

            Order.objects.filter(
                product_id=product_id
            ).delete()

            ProductVariant.objects.filter(
                product_id=product_id
            ).delete()

            Product.objects.filter(
                id=product_id
            ).delete()

            MarketplaceOrder.objects.filter(
                id__in=affected_marketplace_order_ids,
                sub_orders__isnull=True,
            ).delete()

            Customer.objects.filter(
                id__in=affected_customer_ids,
                marketplace_orders__isnull=True,
            ).delete()

        return {
            "success": True,
            "message": "Deleted successfully"
        }
        
        
    # product toggle deactivate-
    # -------------------
    @staticmethod
    def deactivate_product(product_id: int, current_user: User):

        product = Product.objects.filter(
            id=product_id,
            owner=current_user
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        product.is_active = False
        product.updated_by = current_user
        product.save()

        ProductVariant.objects.filter(
            product=product
        ).update(is_active=False)

        return {
            "status": True,
            "message": "Product deactivated successfully"
        }

    def get_image_url(file_key):
        if not file_key:
            return None

        project_url = os.getenv("SUPABASE_PROJECT_URL")
        bucket_name = os.getenv("SUPABASE_S3_BUCKET_NAME")

        return f"{project_url}/storage/v1/object/public/{bucket_name}/{file_key}"