from typing import Optional
from django.contrib.auth.models import User
from api.controllers.pagination_controller import Pagination
from platforms.models import Platform
from products.models import Product, ProductVariant
from fastapi import HTTPException
from api.schemas.product_schema import ProductRequest, ProductResponse, ProductUpdateRequest, ProductVariantResponse
from django.db.models import Q
from django.db import transaction

class ProductController:

    @staticmethod
    def get_product_by_id(product_id: int, current_user: User):
        """
        Fetch single product for current user
        Return None if not found
        """
        product = Product.objects.filter(
            id=product_id, 
            owner=current_user,
            is_active=True
        ).select_related("category", "platform").prefetch_related("variants").first()

        if not product:
            return None
        return product


    @staticmethod
    def get_all_products(
        current_user: User,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        platform: Optional[int] = None
    ):
        try:
            filters = {
                "owner": current_user,
                "is_active": True
            }
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
                    "category_id",
                    "platform_id",
                    "gst_percent",
                    "commission_percent",
                    "is_active",
                    "platform__code"
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
                # get first variant SKU if available
                sku = p.variants.first().sku if p.variants.exists() else None
                category_name = p.category.name if p.category else None
                color= p.variants.first().color if p.variants.exists() else None
                cost_price = p.variants.first().cost_price if p.variants.exists() else None
                stock = p.variants.first().stock if p.variants.exists() else None
                selling_price = p.variants.first().selling_price if p.variants.exists() else None
                
                items.append(
                    ProductResponse(
                        id=p.id,
                        catalog_id=p.catalog_id,
                        name=p.name,
                        category_id=p.category_id,
                        category_name=category_name,   # added category name
                        sku=sku,                  # added SKU
                        color=color,
                        cost_price=cost_price,
                        selling_price=selling_price,
                        stock=stock,
                        platform_code=p.platform.code if p.platform else None,
                        gst_percent=float(p.gst_percent),
                        commission_percent=float(p.commission_percent),
                        is_active=p.is_active,
                        variants=[
                            ProductVariantResponse.model_validate(v)
                            for v in p.variants.all()
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


    @staticmethod
    def update_product_logic(product_id: int, payload: ProductUpdateRequest, current_user: User):
        """
        Update product and its variants. Variants are replaced if provided.
        """
        try:
            product = ProductController.get_product_by_id(product_id, current_user)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            update_data = payload.dict(exclude_unset=True)
           

            # --- Update Product fields ---
            for field, value in update_data.items():
                if field != "variants":
                    if field == "marketplace":
                        setattr(product, "platform_id", value)
                    else:
                        setattr(product, field, value)

            
            if "platform_code" in update_data:
                platform_obj = Platform.objects.filter(code=update_data["platform_code"]).first()
                product.platform = platform_obj
            product.updated_by = current_user
            product.save()

            # --- Update Variants if provided ---
            if "variants" in update_data:
                # Delete old variants
                # product.variants.all().delete()
                
                existing_variants = {v.id: v for v in product.variants.all()}
                incoming_variants = payload.variants or []
                incoming_ids = []
                for variant_data in incoming_variants:
                    variant_id = variant_data.id

                    if variant_id and variant_id in existing_variants:
                        # Update existing variant
                        variant = existing_variants[variant_id]
                        variant.sku = variant_data.sku
                        variant.size = variant_data.size
                        variant.color = variant_data.color
                        variant.cost_price = variant_data.cost_price
                        variant.selling_price = variant_data.selling_price
                        variant.stock = variant_data.stock
                        variant.shipping_cost = variant_data.shipping_cost or 0.0
                        variant.rto_cost = variant_data.rto_cost or 0.0
                        variant.save()
                        incoming_ids.append(variant_id)
                    else:
                        # Create new variant
                        new_variant = ProductVariant.objects.create(
                            product=product,
                            sku=variant_data.sku,
                            size=variant_data.size,
                            color=variant_data.color,
                            cost_price=variant_data.cost_price,
                            selling_price=variant_data.selling_price,
                            stock=variant_data.stock,
                            shipping_cost=variant_data.shipping_cost or 0.0,
                            rto_cost=variant_data.rto_cost or 0.0
                        )

                # Create new variants
                # for variant in update_data["variants"]:
                #     ProductVariant.objects.create(
                #             product=product,
                #             sku=variant["sku"],
                #             size=variant.get("size"),
                #             color=variant.get("color"),
                #             cost_price=variant["cost_price"],
                #             selling_price=variant["selling_price"],
                #             stock=variant["stock"],
                #             shipping_cost=variant.get("shipping_cost", 0.0),
                #             rto_cost=variant.get("rto_cost", 0.0)
                #         )

            # Prefetch variants for response
            product = Product.objects.prefetch_related("variants").get(id=product.id)
            sku = product.variants.first().sku if product.variants.exists() else None
            category_name = product.category.name if product.category else None
            color= product.variants.first().color if product.variants.exists() else None
            cost_price = product.variants.first().cost_price if product.variants.exists() else None
            selling_price = product.variants.first().selling_price if product.variants.exists() else None
            stock = product.variants.first().stock if product.variants.exists() else None
            catalog_id = product.catalog_id if product.catalog_id else None
            platform_code = product.platform.code if product.platform else None
            # Convert to Pydantic schema
            product_response = ProductResponse(
                    id=product.id,
                    catalog_id=product.catalog_id,
                    name=product.name,
                    category_id=product.category_id,
                    category_name=category_name,  # ✅ ADD THIS
                    platform_code=product.platform.code if product.platform else None,  # ✅ also fix this
                    gst_percent=float(product.gst_percent),
                    commission_percent=float(product.commission_percent),
                    sku=sku,
                    color=color,
                    cost_price=cost_price,
                    selling_price=selling_price,
                    stock=stock,
                    is_active=product.is_active,
                    variants=[
                        ProductVariantResponse.model_validate(v)
                        for v in product.variants.all()
                    ]
                )
            return product_response

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while updating product: {str(e)}"
            )
            
    
    @staticmethod
    def delete_product_logic(product_id: int, current_user: User):
        """
        Soft delete product for current user
        """
        product = ProductController.get_product_by_id(product_id, current_user)
        product.soft_delete(user=current_user)  # uses BaseModel soft_delete
        return {"status": "success", "deleted_at": product.deleted_at}

    @staticmethod
    def toggle_product_active_logic(product_id: int, current_user: User):
        """
        Toggle active/inactive status of a product
        """
        product = ProductController.get_product_by_id(product_id, current_user)
        product.is_active = not product.is_active
        product.updated_by = current_user
        product.save()
        return product

    def build_product_response(product):
        product = Product.objects.prefetch_related(
            "variants", "category", "platform"
        ).get(id=product.id)

        first_variant = product.variants.first()

        return ProductResponse(
            id=product.id,
            catalog_id=product.catalog_id,
            name=product.name,
            category_id=product.category_id,
            category_name=product.category.name if product.category else None,
            platform_code=product.platform.code if product.platform else None,
            gst_percent=float(product.gst_percent),
            commission_percent=float(product.commission_percent),
            is_active=product.is_active,

            # First variant data
            sku=first_variant.sku if first_variant else None,
            color=first_variant.color if first_variant else None,
            cost_price=first_variant.cost_price if first_variant else 0,
            selling_price=first_variant.selling_price if first_variant else 0,
            stock=first_variant.stock if first_variant else 0,

            # Variants list
            variants=[
                ProductVariantResponse.model_validate(v)
                for v in product.variants.all()
            ]
        )