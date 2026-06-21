from django.db import transaction
from django.contrib.auth.models import User
from users.models import UserProfile
from api.schemas.user_profile_schema import UserProfileUpdateRequest, UserProfileResponse

class UserProfileController:
    @staticmethod
    def get_profile(current_user: User):
        try:
            profile, created = UserProfile.objects.get_or_create(
                user=current_user,
                defaults={
                    "email": current_user.email,
                    "first_name": current_user.first_name,
                    "last_name": current_user.last_name,
                    "is_active": True
                }
            )
            
            # return {
            #     "success": True,
            #     "data": UserProfileResponse(
            #         username=current_user.username,
            #         first_name=profile.first_name,
            #         last_name=profile.last_name,
            #         email=profile.email,
            #         mobile_number=profile.mobile_number,
            #         created_at=profile.created_at
            #     )
            # }
            return {
                "success": True,
                "data": UserProfileResponse(
                    username=current_user.username,
                    first_name=profile.first_name or current_user.first_name,
                    last_name=profile.last_name or current_user.last_name,
                    email=profile.email or current_user.email,
                    mobile_number=profile.mobile_number,
                    created_at=profile.created_at,
                    trial_start=profile.trial_start,
                    trial_end=profile.trial_end,
                    subscription_start=profile.subscription_start,
                    subscription_end=profile.subscription_end,
                    payment_verified=profile.payment_verified
                )
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error retrieving profile: {str(e)}"
            }

    @staticmethod
    def update_profile(current_user: User, payload: UserProfileUpdateRequest):
        try:
            # If email is updated, ensure it's not already in use by another user
            if payload.email and payload.email.strip().lower() != current_user.email.strip().lower():
                new_email = payload.email.strip().lower()
                if User.objects.filter(email__iexact=new_email).exclude(id=current_user.id).exists():
                    return {
                        "success": False,
                        "message": "Email is already in use by another user"
                    }
            
            with transaction.atomic():
                profile, created = UserProfile.objects.get_or_create(
                    user=current_user,
                    defaults={
                        "is_active": True
                    }
                )
                
                # Update fields if provided
                if payload.first_name is not None:
                    current_user.first_name = payload.first_name.strip()
                    profile.first_name = payload.first_name.strip()
                if payload.last_name is not None:
                    current_user.last_name = payload.last_name.strip()
                    profile.last_name = payload.last_name.strip()
                if payload.email is not None:
                    email_clean = payload.email.strip().lower()
                    current_user.email = email_clean
                    profile.email = email_clean
                if payload.mobile_number is not None:
                    profile.mobile_number = payload.mobile_number.strip()
                
                current_user.save()
                profile.save()
                
            return {
                "success": True,
                "message": "Profile updated successfully",
                "data": UserProfileResponse(
                    username=current_user.username,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    email=profile.email,
                    mobile_number=profile.mobile_number,
                    created_at=profile.created_at
                )
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating profile: {str(e)}"
            }
