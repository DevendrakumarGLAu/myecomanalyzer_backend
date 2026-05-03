"""
Auth Models for secure token management, session control, and abuse protection.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class RefreshToken(models.Model):
    """
    Store refresh tokens in database for rotation and revocation.
    Allows detection of token reuse (possible compromise).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=512, unique=True, db_index=True)
    # Store previous token hash to detect reuse
    revoked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # IP address and user agent for tracking device usage
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "refresh_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"RefreshToken for {self.user.username} - {self.created_at}"

    def is_expired(self):
        """Check if token has expired"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return self.is_active and not self.is_expired() and self.revoked_at is None

    def revoke(self):
        """Revoke the token (on logout)"""
        self.revoked_at = timezone.now()
        self.is_active = False
        self.save()


class TokenBlacklist(models.Model):
    """
    Blacklist compromised or logged-out tokens for additional security.
    Can also store access tokens for compromised account scenarios.
    """
    token_hash = models.CharField(max_length=512, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blacklisted_tokens")
    reason = models.CharField(
        max_length=50,
        choices=[
            ("logout", "User Logout"),
            ("password_change", "Password Changed"),
            ("compromise", "Token Compromised"),
            ("admin_revoke", "Admin Revoked"),
            ("account_lock", "Account Locked"),
        ],
        default="logout"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "token_blacklist"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Blacklisted token for {self.user.username}"


class LoginAttempt(models.Model):
    """
    Track login attempts to enable rate limiting and brute force detection.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_attempts", null=True, blank=True)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=False)
    reason = models.CharField(
        max_length=50,
        choices=[
            ("success", "Successful Login"),
            ("invalid_creds", "Invalid Credentials"),
            ("account_inactive", "Account Inactive"),
            ("account_locked", "Account Locked"),
            ("invalid_email", "Invalid Email"),
        ],
        default="invalid_creds"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "login_attempts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ip_address", "created_at"]),
            models.Index(fields=["email", "created_at"]),
        ]

    def __str__(self):
        return f"{'✓' if self.success else '✗'} {self.email} from {self.ip_address}"


class AccountLock(models.Model):
    """
    Temporary account locks after multiple failed login attempts.
    Prevents brute force attacks.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account_lock")
    locked_at = models.DateTimeField(auto_now_add=True)
    locked_until = models.DateTimeField()
    failed_attempts = models.IntegerField(default=0)
    last_failed_attempt = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(
        max_length=100,
        choices=[
            ("brute_force", "Brute Force Detection"),
            ("admin", "Admin Lock"),
        ],
        default="brute_force"
    )

    class Meta:
        db_table = "account_locks"

    def __str__(self):
        return f"Account lock for {self.user.username} until {self.locked_until}"

    def is_active(self):
        """Check if account is currently locked"""
        return timezone.now() < self.locked_until

    def unlock(self):
        """Unlock the account"""
        self.delete()


class SessionLog(models.Model):
    """
    Log all authentication events for security monitoring and auditing.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="session_logs")
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("login", "Login"),
            ("logout", "Logout"),
            ("token_refresh", "Token Refresh"),
            ("token_revoke", "Token Revoked"),
            ("password_change", "Password Changed"),
            ("account_lock", "Account Locked"),
            ("suspicious_activity", "Suspicious Activity"),
        ]
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("success", "Success"), ("failure", "Failure")],
        default="success"
    )
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "session_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event_type} ({self.status})"
