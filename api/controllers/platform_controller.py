from fastapi import HTTPException

from platforms.models import Platform


class PlatformController:

    @staticmethod
    def list_platforms():
        platforms = Platform.objects.all().order_by("name")
        return {
            "data": [{"id": p.id, "name": p.name, "code": p.code} for p in platforms]
        }

    @staticmethod
    def create_platform(payload, current_user):
        code = payload.code.strip().upper()
        name = payload.name.strip()

        if Platform.objects.filter(code__iexact=code).exists():
            raise HTTPException(status_code=400, detail=f"Platform code '{code}' already exists")

        platform = Platform.objects.create(
            name=name,
            code=code,
            created_by=current_user,
            updated_by=current_user,
        )

        return {
            "success": True,
            "message": "Platform created successfully",
            "data": {"id": platform.id, "name": platform.name, "code": platform.code},
        }
