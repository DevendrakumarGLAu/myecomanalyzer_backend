from django.db import IntegrityError
from api.schemas.category_schema import CategoryRequest, CategoryResponse
from categories.models import Category
from typing import Optional
from django.db.models import Q
from django.contrib.auth.models import User

class CategoryController:
    @staticmethod
    def get_all_category(current_user: User,page: int = 1,limit: int = 10,search: Optional[str] = None, status: str = "active"):
        """
        Fetch all categories for current_user with optional search, paginated.

        status feeds the admin table's Active/Paused tabs ("all" is also
        accepted). Default stays "active" for callers like the product-form's
        category dropdown, which shouldn't offer a deactivated category as an
        option for a new/edited product.
        """
        filters = {
            "created_by": current_user
        }
        if status == "active":
            filters["is_active"] = True
        elif status == "paused":
            filters["is_active"] = False

        query = Category.objects.filter(**filters)

        if search:
            query = query.filter(Q(name__icontains=search))

        total = query.count()
        start = (page - 1) * limit
        end = start + limit
        items = list(query.order_by("id")[start:end])

        return {
            "data": [CategoryResponse.from_orm(c) for c in items],
            "total": total,
            "page": page,
            "limit": limit
        }
        
    @staticmethod
    def add_category(payload: CategoryRequest, current_user: User):

        # Check duplicate category for same user
        if Category.objects.filter(
            name__iexact=payload.name,
            # is_active=True
        ).exists():
            return {
                "success": False,
                "message": "Category already exists"
            }

        try:
            category = Category.objects.create(
                name=payload.name,
                created_by=current_user,
                is_active=True
            )

            return {
                "success": True,
                "message": "Category created successfully",
                "data": CategoryResponse.from_orm(category)
            }

        except Exception as e:
            return {
                "success": False,
                "details":str(e),
                "message": "Database error while creating category"
            }

    @staticmethod
    def update_category(category_id, payload, current_user):
        try:
            # No is_active filter — an admin must be able to rename a
            # deactivated category too (renaming is independent of the
            # active/inactive toggle). Ownership (created_by) was missing
            # entirely before, letting any authenticated user rename any
            # other user's category by ID.
            category = Category.objects.filter(
                id=category_id,
                created_by=current_user,
            ).first()

            if not category:
                return {
                    "success": False,
                    "message": "Category not found",
                    "data": None
                }

            # Check duplicate (excluding current)
            if Category.objects.filter(
                name__iexact=payload.name.strip()
            ).exclude(id=category_id).exists():
                return {
                    "success": False,
                    "message": "Category with this name already exists",
                    "data": None
                }

            category.name = payload.name.strip()
            category.updated_by = current_user
            category.save()

            return {
                "success": True,
                "message": "Category updated successfully",
                "data": CategoryResponse.from_orm(category)
            }

        except Exception as e:
            return {
                "success": False,
                "message": "Error updating category",
                "data": None,
                "details": str(e)
            }

    @staticmethod
    def get_all_categories():
        try:
            categories = Category.objects.filter(is_active=True).values(
                "id", "name"
            )

            return {
                "success": True,
                "data": list(categories)
            }

        except Exception as e:
            return {
                "success": False,
                "message": "Error fetching categories",
                "details": str(e)
            }

    @staticmethod
    def deactivate_category(category_id, current_user):
        try:
            category = Category.objects.filter(id=category_id, is_active=True).first()

            if not category:
                return {
                    "success": False,
                    "message": "Category not found"
                }

            category.is_active = False
            category.updated_by = current_user
            category.save()

            return {
                "success": True,
                "message": "Category deactivated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "message": "Error deactivating category",
                "details": str(e)
            }

    @staticmethod
    def toggle_category_active(category_id, current_user):
        """
        Flip active/inactive status of a category owned by current_user —
        unlike deactivate_category above, this works in both directions.
        """
        category = Category.objects.filter(id=category_id, created_by=current_user).first()

        if not category:
            return {
                "success": False,
                "message": "Category not found"
            }

        category.is_active = not category.is_active
        category.updated_by = current_user
        category.save()

        return {
            "success": True,
            "message": "Category activated" if category.is_active else "Category deactivated",
            "data": CategoryResponse.from_orm(category)
        }