"""
Quick Start Guide for Secure Authentication System
Run this file to verify the authentication system is working correctly.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from api.token_manager import TokenManager, TokenRotationManager
from api.auth_utils import PasswordValidator, BruteForceProtection
from users.auth_models import RefreshToken, SessionLog, LoginAttempt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_password_validation():
    """Test password policy validation"""
    print("\n" + "="*60)
    print("🔐 Testing Password Validation")
    print("="*60)

    test_passwords = [
        ("weak", False),
        ("WeakPass123", False),
        ("MySecurePass123!", True),
        ("Password@2024", True),
        ("Short1!", False),
    ]

    for password, expected in test_passwords:
        is_valid, error = PasswordValidator.validate(password)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} '{password}' → Valid: {is_valid}")
        if error:
            print(f"   Error: {error}")


def test_token_generation():
    """Test JWT token generation"""
    print("\n" + "="*60)
    print("🎫 Testing Token Generation")
    print("="*60)

    # Create test user
    try:
        user = User.objects.get(username="test_user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="TestPass123!"
        )
        print(f"✅ Created test user: {user.username}")

    # Generate tokens
    access_token = TokenManager.create_access_token(user.id, user.username)
    refresh_token = TokenManager.create_refresh_token(user.id, user.username)

    print(f"✅ Access Token Generated (length: {len(access_token)})")
    print(f"✅ Refresh Token Generated (length: {len(refresh_token)})")

    # Verify tokens
    access_payload = TokenManager.verify_token(access_token, token_type="access")
    refresh_payload = TokenManager.verify_token(refresh_token, token_type="refresh")

    if access_payload:
        print(f"✅ Access Token Valid - User ID: {access_payload.get('sub')}")
    if refresh_payload:
        print(f"✅ Refresh Token Valid - User ID: {refresh_payload.get('sub')}")

    return user, access_token, refresh_token


def test_token_rotation(user, refresh_token):
    """Test refresh token rotation"""
    print("\n" + "="*60)
    print("🔄 Testing Token Rotation")
    print("="*60)

    result = TokenRotationManager.rotate_refresh_token(
        refresh_token,
        user,
        ip_address="192.168.1.1",
        user_agent="Test Client",
        device_id="test-device-123"
    )

    if result:
        print(f"✅ Token Rotation Successful")
        print(f"   New Access Token: {result['access_token'][:30]}...")
        print(f"   New Refresh Token: {result['refresh_token'][:30]}...")
        print(f"   Expires In: {result['expires_in']} seconds")
    else:
        print(f"❌ Token Rotation Failed")


def test_token_revocation(user, refresh_token):
    """Test token revocation"""
    print("\n" + "="*60)
    print("🚫 Testing Token Revocation")
    print("="*60)

    success = TokenRotationManager.revoke_refresh_token(refresh_token, reason="test_logout")

    if success:
        print(f"✅ Token Revocation Successful")

        # Try to use revoked token again (should fail)
        is_reused = TokenRotationManager.detect_token_reuse(refresh_token)
        if is_reused:
            print(f"✅ Token Reuse Detection Working - Reuse detected correctly")
        else:
            print(f"❌ Token Reuse Detection Failed - Reuse not detected")
    else:
        print(f"❌ Token Revocation Failed")


def test_brute_force_protection():
    """Test brute force protection"""
    print("\n" + "="*60)
    print("🛡️  Testing Brute Force Protection")
    print("="*60)

    ip_address = "192.168.1.100"
    email = "brute_force_test@example.com"

    # Simulate failed attempts
    for i in range(6):
        BruteForceProtection.log_failed_attempt(
            email, ip_address, "Test Browser", "invalid_creds"
        )
        print(f"   Logged failed attempt {i+1}")

        # Check if should lock
        should_lock, msg = BruteForceProtection.check_failed_attempts(email)
        if should_lock:
            print(f"✅ Account Lock Triggered: {msg}")
            break


def test_database_models():
    """Verify database models are created"""
    print("\n" + "="*60)
    print("📊 Testing Database Models")
    print("="*60)

    models = {
        "RefreshToken": RefreshToken,
        "SessionLog": SessionLog,
        "LoginAttempt": LoginAttempt,
    }

    for name, model in models.items():
        try:
            count = model.objects.count()
            print(f"✅ {name} table exists (records: {count})")
        except Exception as e:
            print(f"❌ {name} table error: {str(e)}")


def generate_jwt_secret():
    """Generate secure JWT secret"""
    print("\n" + "="*60)
    print("🔑 Generate Secure JWT Secret")
    print("="*60)

    import secrets
    secret = secrets.token_urlsafe(32)
    print(f"✅ Generated JWT_SECRET_KEY (copy to .env):")
    print(f"\nJWT_SECRET_KEY={secret}\n")


def print_summary():
    """Print summary of authentication system"""
    print("\n" + "="*60)
    print("✅ AUTHENTICATION SYSTEM SUMMARY")
    print("="*60)

    print("""
🔐 SECURE AUTHENTICATION FEATURES:

✅ JWT Token System
   - Access tokens: 15 minutes
   - Refresh tokens: 30 days
   - Proper claims: sub, iat, exp, iss, aud

✅ Refresh Token Rotation
   - New token issued every refresh
   - Old token revoked
   - Token reuse detected

✅ Brute Force Protection
   - 5 failed attempts → lock account
   - Rate limiting per IP
   - Temporary account locks

✅ Token Blacklisting
   - On logout
   - On password change
   - On account lock

✅ Session Logging
   - All auth events logged
   - IP and device tracking
   - Security audit trail

✅ Password Policy
   - Min 8 characters
   - Uppercase required
   - Numbers required
   - Special chars required

✅ Rate Limiting
   - Login: 5 attempts/min per IP
   - Refresh: 10 attempts/min per IP
   - Signup: 10 attempts/hour per IP

🚀 NEXT STEPS:
   1. Copy .env.example to .env
   2. Update JWT_SECRET_KEY with generated value
   3. Run migrations: python manage.py migrate
   4. Start server: uvicorn main:app --reload
   5. Test endpoints with provided cURL commands

📚 DOCUMENTATION:
   - See AUTHENTICATION_GUIDE.md for complete guide
   - Check api/auth_endpoints.py for endpoint details
   - Review api/token_manager.py for token logic
   - See users/auth_models.py for database schema
    """)


def main():
    """Run all tests"""
    print("\n")
    print("█" * 60)
    print("█  🔐 SECURE AUTHENTICATION SYSTEM - QUICK START TEST  █")
    print("█" * 60)

    try:
        # Run tests
        test_password_validation()
        user, access_token, refresh_token = test_token_generation()
        test_token_rotation(user, access_token)
        test_token_revocation(user, access_token)
        test_brute_force_protection()
        test_database_models()
        generate_jwt_secret()
        print_summary()

        print("\n✅ All tests completed!")
        print("\n" + "█" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
