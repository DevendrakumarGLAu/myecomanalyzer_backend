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

                items.append(
                    ProductResponse(
                        id=p.id,
                        catalog_id=p.catalog_id,
                        name=p.name,
                        category_id=p.category_id,
                        category_name=category_name,   # added category name
                        sku=sku,                  # added SKU
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

    from django.db import transaction

    @staticmethod
    def add_product(payload: ProductRequest, current_user: User):
        try:
            with transaction.atomic():

                platform_obj = None
                if payload.platform_code:
                    platform_obj = Platform.objects.filter(code=payload.platform_code).first()

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

                variants = []
                for variant in payload.variants:
                    variants.append(
                        ProductVariant(
                            product=product,
                            sku=variant.sku,
                            size=variant.size,
                            color=variant.color,
                            cost_price=variant.cost_price,
                            selling_price=variant.selling_price,
                            stock=variant.stock,
                            shipping_cost=variant.shipping_cost or 0.0,
                            rto_cost=variant.rto_cost or 0.0
                        )
                    )

                ProductVariant.objects.bulk_create(variants)

                product = Product.objects.prefetch_related("variants").get(id=product.id)

                return product

        except Exception as e:
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
                product.variants.all().delete()

                # Create new variants
                for variant in update_data["variants"]:
                    ProductVariant.objects.create(
                            product=product,
                            sku=variant["sku"],
                            size=variant.get("size"),
                            color=variant.get("color"),
                            cost_price=variant["cost_price"],
                            selling_price=variant["selling_price"],
                            stock=variant["stock"],
                            shipping_cost=variant.get("shipping_cost", 0.0),
                            rto_cost=variant.get("rto_cost", 0.0)
                        )

            # Prefetch variants for response
            product = Product.objects.prefetch_related("variants").get(id=product.id)

            # Convert to Pydantic schema
            product_response = ProductResponse(
                id=product.id,
                catalog_id=product.catalog_id,
                name=product.name,
                category_id=product.category_id,
                marketplace=product.platform_id,
                gst_percent=float(product.gst_percent),
                commission_percent=float(product.commission_percent),
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


# from typing import Optional
# from django.contrib.auth.models import User
# from products.models import Product, ProductVariant
# from fastapi import HTTPException
# from api.schemas.product_schema import ProductRequest, ProductResponse, ProductUpdateRequest, ProductVariantResponse
# from django.db.models import Q
# from django.db import transaction

# class ProductController:

#     @staticmethod
#     def get_product_by_id(product_id: int, current_user: User):
#         """
#         Fetch single product for current user
#         Return [] if not found
#         """
#         product = Product.objects.filter(
#             id=product_id, 
#             created_by=current_user, 
#             is_active=True
#         ).first()  # returns None if not found

#         if not product:
#             return []  # return empty list instead of raising 404

#         return product


#     @staticmethod
#     def get_all_products(
#         current_user: User,
#         page: int = 1,
#         limit: int = 10,
#         search: Optional[str] = None,
#         platform: Optional[str] = None
#     ):

#         try:
#             filters = {
#                 "owner": current_user,
#                 "is_active": True
#             }

#             if platform:
#                 filters["platform"] = platform

#             query = (
#                 Product.objects
#                 .filter(**filters)
#                 .select_related("category")
#                 .prefetch_related("variants")
#             )

#             if search:
#                 search_query = (
#                     Q(name__icontains=search) |
#                     Q(catalog_id__icontains=search) |
#                     Q(category__name__icontains=search) |
#                     Q(variants__sku__icontains=search)
#                 )

#                 query = query.filter(search_query).distinct()

#             total = query.count()

#             start = (page - 1) * limit
#             end = start + limit

#             products = query[start:end]

#             items = []

#             for p in products:
#                 items.append(
#                     ProductResponse(
#                         id=p.id,
#                         catalog_id=p.catalog_id,
#                         name=p.name,
#                         category_id=p.category_id,
#                         is_active=p.is_active,
#                         variants=[
#                             ProductVariantResponse.model_validate(v)
#                             for v in p.variants.all()
#                         ]
#                     )
#                 )

#             return {
#                 "items": items,
#                 "total": total,
#                 "page": page,
#                 "limit": limit
#             }

#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error fetching products: {str(e)}"
#             )
        
    
#     @staticmethod
#     def update_product_logic(product_id: int, payload: ProductUpdateRequest, current_user: User):

#         try:
#             with transaction.atomic():

#                 product = ProductController.get_product_by_id(product_id, current_user)

#                 update_data = payload.dict(exclude_unset=True)

#                 # ---- Update Product Fields ----
#                 for field, value in update_data.items():
#                     if field != "variants":
#                         setattr(product, field, value)

#                 product.updated_by = current_user
#                 product.save()

#                 # ---- Update Variants ONLY if provided ----
#                 if "variants" in update_data:

#                     # Option 1 (simple replace)
#                     product.variants.all().delete()

#                     for variant in update_data["variants"]:
#                         ProductVariant.objects.create(
#                             product=product,
#                             sku=variant["sku"],
#                             size=variant.get("size"),
#                             color=variant.get("color"),
#                             cost_price=variant["cost_price"],
#                             selling_price=variant["selling_price"],
#                             stock=variant["stock"]
#                         )

#             return {
#                 "success": True,
#                 "message": "Product updated successfully",
#                 "data": product
#             }

#         except Product.DoesNotExist:
#             raise HTTPException(status_code=404, detail="Product not found")

#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error while updating product: {str(e)}"
#             )

    

#     @staticmethod
#     def add_product(payload: ProductRequest, current_user: User):
#         try:
#             product = Product.objects.create(
#                 catalog_id=payload.catalog_id,
#                 name=payload.name,
#                 category_id=payload.category_id,
#                 owner=current_user,
#                 created_by=current_user,
#                 updated_by=current_user,
#                 is_active=payload.is_active
#             )

#             for variant in payload.variants:
#                 ProductVariant.objects.create(
#                     product=product,
#                     sku=variant.sku,
#                     size=variant.size,
#                     color=variant.color,
#                     cost_price=variant.cost_price,
#                     selling_price=variant.selling_price,
#                     stock=variant.stock
#                 )

#             # load variants for response
#             product = Product.objects.prefetch_related("variants").get(id=product.id)

#             return product

#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error while creating product: {str(e)}"
#             )