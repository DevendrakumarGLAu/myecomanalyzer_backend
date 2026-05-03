from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .auth_models import *

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    payment_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = "user_profile"

    def has_active_trial(self):
        now = timezone.now()
        return self.trial_start and self.trial_end and self.trial_start <= now <= self.trial_end

    def has_active_subscription(self):
        now = timezone.now()
        return self.payment_verified and self.subscription_start and self.subscription_end and self.subscription_start <= now <= self.subscription_end