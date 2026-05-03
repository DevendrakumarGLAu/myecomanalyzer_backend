# 🔐 Secure Authentication System - Complete Setup Guide

## Overview

This is a production-grade JWT authentication system for Django + FastAPI with advanced security features including:

- ✅ Access + Refresh Token Flow (15 min / 30 days)
- ✅ Token Rotation with Compromise Detection
- ✅ Rate Limiting & Brute Force Protection
- ✅ Account Locking after Failed Attempts
- ✅ Token Blacklisting & Revocation
- ✅ HttpOnly Secure Cookies for Token Storage
- ✅ Comprehensive Audit Logging
- ✅ Password Policy Enforcement
- ✅ User Enumeration Prevention
- ✅ Security Headers & CORS Protection

---

## 🚀 Installation & Setup

### Step 1: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install packages
pip install -r requirements.txt

# Install Argon2 for better password hashing (optional but recommended)
pip install argon2-cffi
```

### Step 2: Environment Variables

Create a `.env` file in the project root:

```env
# ===== JWT Configuration =====
JWT_SECRET_KEY=your-super-secret-key-change-in-production-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# ===== Django =====
DEBUG=False
SECRET_KEY=django-insecure-your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://yourdomain.com

# ===== Database =====
DB_ENGINE=django.db.backends.postgresql
DB_NAME=myecomanalyzer
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# ===== Security =====
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# ===== Logging =====
LOG_LEVEL=INFO
```

### Step 3: Run Migrations

```bash
# Navigate to project directory
cd backend

# Apply migrations to create auth models
python manage.py migrate

# Or run specific migration
python manage.py migrate users 0002_secure_auth_models
```

### Step 4: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### Step 5: Start Development Server

```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: FastAPI server (if using separate)
uvicorn main:app --reload
```

---

## 🔑 Authentication Flow

### 1. User Registration (Signup)

**📝 Request:**
```bash
POST /api/auth/signup
Content-Type: application/json

{
    "email": "user@example.com",
    "username": "john_doe",
    "password": "MySecurePass123!",
    "password_confirm": "MySecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

**✅ Response (200):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900,
    "user_id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Password Policy:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)
- Cannot contain common patterns

### 2. User Login

**📝 Request:**
```bash
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "MySecurePass123!",
    "device_id": "device-uuid-123",
    "remember_me": false
}
```

**✅ Response (200):**
Same as signup response

**❌ Error Responses:**
```json
// 429 - Too many attempts
{
    "detail": "Too many requests from this IP. Try again in 45 seconds"
}

// 403 - Account locked
{
    "detail": "Account locked due to multiple failed attempts. Try again in 30 minutes"
}

// 401 - Invalid credentials (generic to prevent user enumeration)
{
    "detail": "Invalid credentials"
}
```

**Rate Limiting:**
- 5 attempts per minute per IP
- 5 failed attempts within 15 minutes → account lock for 30 minutes
- After accounts unlock, counter resets

### 3. Access Protected Routes

**Using Access Token in Header:**
```bash
GET /api/users/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**FastAPI Dependency:**
```python
from api.auth import get_current_user

@app.get("/users/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }
```

### 4. Refresh Token

**📝 Request:**
```bash
POST /api/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "device_id": "device-uuid-123"
}
```

**✅ Response (200):**
```json
{
    "access_token": "new-eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "new-eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
}
```

**Security Features:**
- Old refresh token is revoked
- Each refresh issues a NEW refresh token (rotation)
- Detects token reuse (possible compromise)
- Tokens can only be used once

### 5. Logout

**📝 Request:**
```bash
POST /api/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**✅ Response (200):**
```json
{
    "message": "Logout successful"
}
```

---

## 🛡️ Security Features Explained

### 1. JWT Token Structure

**Access Token Claims:**
```json
{
    "sub": "123",           // User ID
    "username": "john_doe",
    "type": "access",
    "iat": 1234567890,     // Issued at
    "exp": 1234568790,     // Expiration
    "iss": "ecomm-profit", // Issuer
    "aud": "ecomm-profit-api" // Audience
}
```

**Refresh Token Claims:**
```json
{
    "sub": "123",
    "username": "john_doe",
    "type": "refresh",
    "iat": 1234567890,
    "exp": 1234654290,     // 30 days
    "iss": "ecomm-profit",
    "aud": "ecomm-profit-api"
}
```

### 2. Refresh Token Rotation

```
User Login
    ↓
Issue Access + Refresh Token (RT1)
Store RT1 in DB
    ↓
Access Token expires (after 15 min)
    ↓
User sends RT1 for refresh
    ↓
Verify RT1 (not revoked, not expired)
    ↓
Revoke RT1 in DB
    ↓
Issue new Access + Refresh Token (RT2)
Store RT2 in DB
    ↓
Return new tokens to client
```

**If old RT used again (reuse detected):**
```
User sends RT1 again
    ↓
Check if RT1 is revoked → YES
    ↓
ALERT: Possible token compromise
    ↓
Return 403 Forbidden
```

### 3. Brute Force Protection

**Detection Flow:**
```
Failed Login Attempt
    ↓
Log attempt (email, IP, timestamp)
    ↓
Count failed attempts in last 15 min
    ↓
If count >= 5:
    └─→ Lock account for 30 minutes
    └─→ Log security event
    └─→ Return 403 Forbidden
```

**Tracking:**
- Per email + IP combination
- Failed attempts stored in `login_attempts` table
- Account lock stored in `account_locks` table
- Manual unlock possible by admin

### 4. Token Blacklisting

**When Added to Blacklist:**
- On logout
- On password change
- On account lock
- On token compromise detection

**Stored In `token_blacklist` Table:**
- Token hash (never store raw token)
- User reference
- Reason for blacklist
- Expiration time

**Cleanup:**
- Expired entries removed after expiration
- Automatic cleanup job (can be Celery task)

### 5. Secure Cookie Storage

**HttpOnly Cookie Flags:**
```
Set-Cookie: refresh_token=xyz123; 
    HttpOnly;           // JavaScript cannot access
    Secure;             // HTTPS only
    SameSite=Strict;    // CSRF protection
    Path=/;
    Max-Age=2592000     // 30 days
```

**Benefits:**
- XSS attacks cannot steal tokens
- CSRF attacks prevented by SameSite
- HTTPS-only prevents man-in-the-middle

### 6. Session Logging & Monitoring

**Events Logged:**
- Login (success/failure)
- Logout
- Token refresh
- Token revocation
- Password change
- Account lock
- Suspicious activity

**Audit Information Stored:**
- User ID
- Event type
- Timestamp
- IP address
- User agent
- Device ID
- Event status
- Additional details (JSON)

---

## 📊 Database Schema

### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id BIGINT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(512) UNIQUE NOT NULL,
    revoked_at TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    INDEX (user_id, is_active),
    INDEX (expires_at)
);
```

### token_blacklist
```sql
CREATE TABLE token_blacklist (
    id BIGINT PRIMARY KEY,
    token_hash VARCHAR(512) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    reason VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    INDEX (token_hash),
    INDEX (expires_at)
);
```

### login_attempts
```sql
CREATE TABLE login_attempts (
    id BIGINT PRIMARY KEY,
    user_id INT,
    email VARCHAR(255),
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE,
    reason VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    INDEX (ip_address, created_at),
    INDEX (email, created_at)
);
```

### account_locks
```sql
CREATE TABLE account_locks (
    id BIGINT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    locked_at TIMESTAMP NOT NULL,
    locked_until TIMESTAMP NOT NULL,
    failed_attempts INT DEFAULT 0,
    last_failed_attempt TIMESTAMP NULL,
    reason VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);
```

### session_logs
```sql
CREATE TABLE session_logs (
    id BIGINT PRIMARY KEY,
    user_id INT NOT NULL,
    event_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_id VARCHAR(255),
    status VARCHAR(20),
    details JSON,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    INDEX (user_id, created_at),
    INDEX (event_type, created_at)
);
```

---

## 🔧 Configuration Reference

### JWT Settings (in .env)
```env
JWT_SECRET_KEY=                          # Minimum 32 characters
JWT_ALGORITHM=HS256                      # or RS256 for asymmetric
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15       # 5-15 minutes recommended
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30         # 7-30 days recommended
```

### Security Settings (in settings.py)
```python
# Rate Limiting
RATE_LIMIT_LOGIN_PER_MINUTE = 5          # Per IP address
RATE_LIMIT_REFRESH_TOKEN_PER_MINUTE = 10
RATE_LIMIT_SIGNUP_PER_HOUR = 10

# Brute Force
FAILED_LOGIN_ATTEMPTS_LIMIT = 5
FAILED_LOGIN_WINDOW_MINUTES = 15
ACCOUNT_LOCK_DURATION_MINUTES = 30

# Password Policy
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True
```

---

## 🚨 Common Scenarios & Responses

### Scenario 1: Token Expired
```
GET /api/users/profile
Authorization: Bearer <expired-token>

Response (401):
{
    "detail": "Invalid or expired token"
}
```
**Action:** Client should use refresh token to get new access token.

### Scenario 2: Token Reuse Detected
```
POST /api/auth/refresh
{
    "refresh_token": "<old-revoked-token>"
}

Response (403):
{
    "detail": "Token reuse detected. Please login again for security."
}
```
**Action:** Possible compromise. User must login again.

### Scenario 3: Account Locked
```
POST /api/auth/login
{
    "email": "user@example.com",
    "password": "correct-password"
}

Response (403):
{
    "detail": "Account locked due to multiple failed attempts. Try again in 28 minutes"
}
```
**Action:** Wait for lock to expire or admin unlock.

### Scenario 4: Rate Limit Exceeded
```
POST /api/auth/login (5th request within 1 minute)

Response (429):
{
    "detail": "Too many requests from this IP. Try again in 45 seconds"
}
```
**Action:** Exponential backoff recommended.

---

## 📝 Using Authenticated Endpoints

### Example 1: Getting User Profile

```python
# FastAPI endpoint
from fastapi import Depends
from api.auth import get_current_user

@app.get("/api/users/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
    }
```

**Request:**
```bash
curl -X GET http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer <access-token>"
```

### Example 2: Admin-Only Endpoint

```python
async def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.get("/api/admin/stats")
async def get_stats(admin: User = Depends(get_current_admin)):
    # Only accessible by admin users
    return {"stats": [...]}
```

### Example 3: Optional Authentication

```python
from api.auth import get_current_user_optional

@app.get("/api/posts")
async def get_posts(current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        # Show personalized posts
        return {"posts": [...], "personalized": True}
    else:
        # Show public posts
        return {"posts": [...], "personalized": False}
```

---

## 🧪 Testing

### Running Tests
```bash
python manage.py test users.tests
python manage.py test api.tests
```

### Manual Testing with cURL

```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# 3. Use access token
curl -X GET http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer <access-token>"

# 4. Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh-token>"}'

# 5. Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh-token>"}'
```

---

## 📚 Advanced Usage

### Custom Claims

```python
from api.token_manager import TokenManager

# Add custom claims
additional_claims = {
    "role": "admin",
    "permissions": ["read", "write"],
}

token = TokenManager.create_access_token(
    user_id=user.id,
    username=user.username,
    additional_claims=additional_claims
)
```

### Token Cleanup (Celery Task)

```python
from celery import shared_task
from api.token_manager import TokenCleanupManager

@shared_task
def cleanup_expired_tokens():
    stats = TokenCleanupManager.cleanup_expired_tokens()
    print(f"Cleaned up: {stats}")
```

### Invalidate All User Tokens

```python
from api.token_manager import TokenRotationManager

# On password change
TokenRotationManager.invalidate_user_tokens(user, reason="password_change")
```

---

## ⚠️ Security Checklist

- [ ] Changed `JWT_SECRET_KEY` to random 32+ character string
- [ ] Enabled `SECURE_SSL_REDIRECT = True` in production
- [ ] Set `DEBUG = False` in production
- [ ] Configured `ALLOWED_HOSTS` for your domain
- [ ] Set up HTTPS certificates
- [ ] Configured database with strong password
- [ ] Set up log rotation and monitoring
- [ ] Regular security updates (`pip install --upgrade -r requirements.txt`)
- [ ] Enable rate limiting (Redis recommended for production)
- [ ] Monitor `security.log` for suspicious activity
- [ ] Regular audit of `session_logs` table
- [ ] Set up alerts for failed login attempts

---

## 🆘 Troubleshooting

### "Invalid token format"
- Ensure Authorization header is: `Authorization: Bearer <token>`
- Check token is not expired

### "Too many attempts"
- Wait for rate limit window (1 minute for login)
- Check IP is not blocked

### "Account locked"
- Wait 30 minutes for automatic unlock
- Admin can unlock with `AccountLock.unlock()`

### Migrations Error
- Run: `python manage.py showmigrations users`
- Run: `python manage.py migrate users`

---

## 📞 Support

For issues or questions:
1. Check security.log for error details
2. Review database tables for audit trail
3. Check rate limit settings
4. Verify JWT_SECRET_KEY is set

---

**Last Updated:** May 2, 2026
**Version:** 1.0.0 - Production Ready
