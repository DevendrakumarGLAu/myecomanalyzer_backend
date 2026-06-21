from django.utils.timezone import now
from django.db import transaction
from users.models import UserProfile
from django.contrib.auth.models import User


class SubscriptionController:

    @staticmethod
    def get_subscription(current_user: User):
        try:
            profile, created = UserProfile.objects.get_or_create(
                user=current_user,
                defaults={"is_active": True}
            )

            current_time = now()

            # -------------------------
            # DETERMINE STATUS
            # -------------------------
            status = "FREE"
            plan = "FREE"

            # Trial logic
            if profile.trial_end and profile.trial_end > current_time:
                status = "TRIAL"
                plan = "TRIAL"

            # Subscription logic
            if profile.subscription_end and profile.subscription_end > current_time:
                status = "ACTIVE"
                plan = "PRO"

            # Expired logic
            if (profile.trial_end and profile.trial_end < current_time) and not profile.subscription_end:
                status = "EXPIRED"

            # -------------------------
            # DAYS LEFT CALCULATION
            # -------------------------
            end_date = profile.subscription_end or profile.trial_end
            days_left = 0

            if end_date:
                days_left = (end_date - current_time).days

            return {
                "success": True,
                "data": {
                    "username": current_user.username,
                    "email": current_user.email,

                    "plan": plan,
                    "status": status,

                    "trial_start": profile.trial_start,
                    "trial_end": profile.trial_end,

                    "subscription_start": profile.subscription_start,
                    "subscription_end": profile.subscription_end,

                    "payment_verified": profile.payment_verified,
                    "is_active": profile.is_active,

                    "days_left": max(days_left, 0),
                    "is_expired": days_left < 0
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error fetching subscription: {str(e)}"
            }

    @staticmethod
    def renew_subscription(current_user: User, plan: str):
        try:
            profile = UserProfile.objects.get(user=current_user)

            with transaction.atomic():

                # Example: PRO plan = 30 days
                from datetime import timedelta
                from django.utils.timezone import now

                start = now()
                end = start + timedelta(days=30)

                profile.subscription_start = start
                profile.subscription_end = end
                profile.payment_verified = False  # set true after payment gateway callback

                profile.save()

            return {
                "success": True,
                "message": "Subscription initiated",
                "data": {
                    "plan": plan,
                    "payment_required": True,
                    "subscription_end": profile.subscription_end
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }