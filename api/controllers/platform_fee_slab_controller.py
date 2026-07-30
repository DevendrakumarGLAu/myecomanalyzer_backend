from fastapi import HTTPException

from platform_fees.models import PlatformFeeSlab
from platforms.models import Platform


def _to_response(slab: PlatformFeeSlab) -> dict:
    return {
        "id": slab.id,
        "platform_code": slab.platform.code,
        "platform_name": slab.platform.name,
        "category": slab.category,
        "min_selling_price": float(slab.min_selling_price),
        "max_selling_price": float(slab.max_selling_price) if slab.max_selling_price is not None else None,
        "commission_percent": float(slab.commission_percent),
        "fixed_fee": float(slab.fixed_fee),
        "shipping_fee": float(slab.shipping_fee),
        "rto_fee": float(slab.rto_fee),
        "gst_percent": float(slab.gst_percent),
        "effective_from": slab.effective_from,
        "is_active": slab.is_active,
    }


class PlatformFeeSlabController:

    @staticmethod
    def list_slabs(platform_code=None, include_inactive=False):
        query = PlatformFeeSlab.objects.select_related("platform")

        if not include_inactive:
            query = query.filter(is_active=True)

        if platform_code:
            query = query.filter(platform__code__iexact=platform_code)

        slabs = list(query)

        return {
            "total": len(slabs),
            "data": [_to_response(s) for s in slabs],
        }

    @staticmethod
    def create_slab(payload, current_user):
        platform = Platform.objects.filter(code__iexact=payload.platform_code).first()
        if not platform:
            raise HTTPException(status_code=404, detail=f"Platform '{payload.platform_code}' not found")

        if payload.max_selling_price is not None and payload.max_selling_price <= payload.min_selling_price:
            raise HTTPException(status_code=400, detail="max_selling_price must be greater than min_selling_price")

        slab = PlatformFeeSlab.objects.create(
            platform=platform,
            category=(payload.category or "ALL").strip() or "ALL",
            min_selling_price=payload.min_selling_price,
            max_selling_price=payload.max_selling_price,
            commission_percent=payload.commission_percent,
            fixed_fee=payload.fixed_fee,
            shipping_fee=payload.shipping_fee,
            rto_fee=payload.rto_fee,
            gst_percent=payload.gst_percent,
            effective_from=payload.effective_from,
            created_by=current_user,
            updated_by=current_user,
        )

        return {
            "success": True,
            "message": "Fee slab created successfully",
            "data": _to_response(slab),
        }

    @staticmethod
    def update_slab(slab_id, payload, current_user):
        slab = PlatformFeeSlab.objects.select_related("platform").filter(id=slab_id).first()
        if not slab:
            raise HTTPException(status_code=404, detail="Fee slab not found")

        platform = Platform.objects.filter(code__iexact=payload.platform_code).first()
        if not platform:
            raise HTTPException(status_code=404, detail=f"Platform '{payload.platform_code}' not found")

        if payload.max_selling_price is not None and payload.max_selling_price <= payload.min_selling_price:
            raise HTTPException(status_code=400, detail="max_selling_price must be greater than min_selling_price")

        slab.platform = platform
        slab.category = (payload.category or "ALL").strip() or "ALL"
        slab.min_selling_price = payload.min_selling_price
        slab.max_selling_price = payload.max_selling_price
        slab.commission_percent = payload.commission_percent
        slab.fixed_fee = payload.fixed_fee
        slab.shipping_fee = payload.shipping_fee
        slab.rto_fee = payload.rto_fee
        slab.gst_percent = payload.gst_percent
        slab.effective_from = payload.effective_from
        slab.updated_by = current_user
        slab.save()

        return {
            "success": True,
            "message": "Fee slab updated successfully",
            "data": _to_response(slab),
        }

    @staticmethod
    def toggle_active(slab_id, current_user):
        slab = PlatformFeeSlab.objects.select_related("platform").filter(id=slab_id).first()
        if not slab:
            raise HTTPException(status_code=404, detail="Fee slab not found")

        slab.is_active = not slab.is_active
        slab.updated_by = current_user
        slab.save()

        return {
            "success": True,
            "message": "Fee slab activated" if slab.is_active else "Fee slab deactivated",
            "data": _to_response(slab),
        }

    @staticmethod
    def delete_slab(slab_id, current_user):
        # Soft delete — keeps historical rate data intact rather than losing
        # it, consistent with effective_from's purpose of tracking rate changes.
        slab = PlatformFeeSlab.objects.filter(id=slab_id).first()
        if not slab:
            raise HTTPException(status_code=404, detail="Fee slab not found")

        slab.soft_delete(user=current_user)

        return {"success": True, "message": "Fee slab deleted successfully"}
