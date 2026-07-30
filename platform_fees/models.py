from django.db import models

from api.base import BaseModel


class PlatformFeeSlab(BaseModel):
    """
    One price-band fee rule for a platform, matching how marketplaces
    actually publish their fee charts (a price range -> commission % + fixed
    fee + shipping fee, bundled together). The public profit calculator looks
    up the matching slab for (platform, category, selling_price) and computes
    from it — adding a new platform or updating a rate is a data change here,
    not a code change.
    """

    platform = models.ForeignKey("platforms.Platform", on_delete=models.CASCADE, related_name="fee_slabs")
    # "ALL" applies to every category on this platform; a specific category
    # name overrides "ALL" for that category when present.
    category = models.CharField(max_length=100, default="ALL")

    min_selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    # null = no upper bound (this is the top-most slab for the platform/category)
    max_selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rto_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=18)

    # Lets a rate change be recorded without deleting the old slab's history —
    # the calculator always uses the most recent slab whose effective_from
    # has passed.
    effective_from = models.DateField()

    class Meta:
        db_table = "platform_fee_slabs"
        ordering = ["platform_id", "category", "min_selling_price"]
        indexes = [
            models.Index(fields=["platform", "category", "min_selling_price"]),
        ]

    def __str__(self):
        return f"{self.platform.code} / {self.category} / {self.min_selling_price}-{self.max_selling_price or '∞'}"
