from django.db import models

from platforms.models import Platform
from django.contrib.auth.models import User
# Create your models here.
class AdsSpend(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)

    campaign_id = models.CharField(max_length=100)

    deduction_duration = models.DateField(null=True, blank=True)
    deduction_date = models.DateField(null=True, blank=True)

    ad_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credits = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    ad_cost_after_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_ads_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ads_spend"
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "campaign_id", "deduction_duration"],
                name="unique_ads_spend_entry"
            )
        ]
