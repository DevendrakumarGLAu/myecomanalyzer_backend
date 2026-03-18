from typing import Dict, Any
from django.db.models import QuerySet
import math


class Pagination:

    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 100

    @staticmethod
    def paginate(queryset: QuerySet, page: int = 1, limit: int = 10) -> Dict[str, Any]:

        page = max(page or Pagination.DEFAULT_PAGE, 1)
        limit = min(limit or Pagination.DEFAULT_LIMIT, Pagination.MAX_LIMIT)

        total = queryset.count()

        start = (page - 1) * limit
        end = start + limit

        items = queryset[start:end]

        total_pages = math.ceil(total / limit) if total else 1

        return {
            "queryset": items,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        }