# System Architecture & Flow Diagrams

## 1. Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

CLIENT SIDE                          SERVER SIDE
───────────────────────────────────────────────────────────────────

                          REGISTRATION
User enters credentials
         │
         ├─→ POST /auth/signup ──→ ┌─────────────────────────┐
                                   │ Validate Input:         │
                                   │ - Email format ✓        │
                                   │ - Username unique ✓     │
                                   │ - Password policy ✓     │
                                   └──────────┬──────────────┘
                                              │
                                   ┌──────────▼──────────────┐
                                   │ Create User:            │
                                   │ - Password hash (bcrypt)│
                                   │ - UserProfile           │
                                   └──────────┬──────────────┘
                                              │
                                   ┌──────────▼──────────────┐
                                   │ Generate Tokens:        │
                                   │ - Access (15 min)       │
                                   │ - Refresh (30 days)     │
                                   └──────────┬──────────────┘
                                              │
                          Return Tokens ←─────┘
         │
         └── Store tokens (secure)
             
───────────────────────────────────────────────────────────────────

                            LOGIN
User enters email/password
         │
         ├─→ POST /auth/login ──→ ┌─────────────────────────┐
                                  │ Rate Limit Check:       │
                                  │ - Per IP ✓              │
                                  │ - Per Email ✓           │
                                  └──────────┬──────────────┘
                                             │
                                  ┌──────────▼──────────────┐
                                  │ Find User:              │
                                  │ - By email              │
                                  │ - Check active ✓        │
                                  └──────────┬──────────────┘
                                             │
                                  ┌──────────▼──────────────┐
                                  │ Verify Password:        │
                                  │ - Constant-time compare │
                                  │ - Log attempt           │
                                  └──────────┬──────────────┘
                                             │
                                  ┌──────────▼──────────────┐
                                  │ Check Account Lock:     │
                                  │ - Lock exists? ✓        │
                                  │ - Still locked? ✓       │
                                  └──────────┬──────────────┘
                                             │
                                  ┌──────────▼──────────────┐
                                  │ Create Tokens:          │
                                  │ - Access Token          │
                                  │ - Refresh Token         │
                                  │ - Store in DB           │
                                  └──────────┬──────────────┘
                                             │
                              Return Tokens ←─────┘
         │
         └── Store securely

───────────────────────────────────────────────────────────────────

                      PROTECTED API CALL
GET /api/users/profile
Authorization: Bearer <access-token>
         │
         ├─→ FastAPI Middleware ──→ ┌─────────────────────────┐
                                    │ Extract Token:          │
                                    │ - From Authorization    │
                                    │ - Validate format ✓     │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │ Verify Signature:       │
                                    │ - JWT signature ✓       │
                                    │ - Expiry check ✓        │
                                    │ - Type check ✓          │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │ Check Blacklist:        │
                                    │ - Token revoked? ✓      │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │ Extract User:           │
                                    │ - From token claim      │
                                    │ - Fetch from DB         │
                                    │ - Check active ✓        │
                                    └────────────┬────────────┘
                                                 │
                              Allow Request ←────┘
         │
         └── Process and Return Response


───────────────────────────────────────────────────────────────────

                       TOKEN REFRESH
POST /auth/refresh
{
    "refresh_token": "<token>"
}
         │
         ├─→ Refresh Handler ──→ ┌──────────────────────────┐
                                 │ Verify Token:            │
                                 │ - Signature ✓            │
                                 │ - Type: refresh ✓        │
                                 │ - Expiry ✓               │
                                 └──────────┬───────────────┘
                                            │
                                 ┌──────────▼───────────────┐
                                 │ Check Reuse:            │
                                 │ - In blacklist? ✓        │
                                 │ - Token reuse alert!     │
                                 └──────────┬───────────────┘
                                            │
                                 ┌──────────▼───────────────┐
                                 │ Revoke Old Token:        │
                                 │ - Mark revoked in DB     │
                                 │ - Add to blacklist       │
                                 └──────────┬───────────────┘
                                            │
                                 ┌──────────▼───────────────┐
                                 │ Create New Tokens:       │
                                 │ - New access token       │
                                 │ - New refresh token      │
                                 │ - Store in DB            │
                                 └──────────┬───────────────┘
                                            │
                            Return New Tokens ←─────┘
         │
         └── Update stored tokens

───────────────────────────────────────────────────────────────────

                         LOGOUT
POST /auth/logout
Authorization: Bearer <access-token>
         │
         ├─→ Logout Handler ──→ ┌──────────────────────────┐
                                │ Get User from Token:     │
                                │ - Extract user ID        │
                                └────────┬─────────────────┘
                                         │
                                ┌────────▼─────────────────┐
                                │ Revoke Refresh Token:    │
                                │ - Mark revoked          │
                                │ - Add to blacklist      │
                                └────────┬─────────────────┘
                                         │
                                ┌────────▼─────────────────┐
                                │ Log Session:            │
                                │ - Event: logout         │
                                │ - Timestamp, IP         │
                                └────────┬─────────────────┘
                                         │
                              Success Response ←─────┘
         │
         └── Clear stored tokens
```

---

## 2. Brute Force Protection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│               BRUTE FORCE PROTECTION FLOW                        │
└─────────────────────────────────────────────────────────────────┘

Failed Login Attempt
         │
         ▼
┌─────────────────────────────────┐
│ Log Attempt to LoginAttempt DB  │
│ - Email                         │
│ - IP Address                    │
│ - Timestamp                     │
│ - Reason: invalid_creds         │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Query Last 15 Minutes           │
│ SELECT COUNT(*) FROM            │
│ login_attempts WHERE            │
│ email = ? AND created_at > ...  │
└──────────────┬──────────────────┘
               │
        ┌──────┴──────┬──────┐
        │             │      │
        ▼             ▼      ▼
    Count: 1-4   Count: 5   Count: 5+
        │             │      │
    ALLOW        LOCK ACC  ERROR
    Login        Lock User  (Already
                 for 30min  Locked)
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
    Create Unlock     User tries
    Timer Event       to login
                        │
                        ▼
                    Account
                    Still Locked
                     (Reject)
                        │
                        ▼
                    Wait for
                    automatic
                    unlock
```

---

## 3. Rate Limiting Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  RATE LIMITING ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

REQUEST ARRIVES
       │
       ▼
┌──────────────────────────┐
│ Extract Client IP        │
│ - X-Forwarded-For        │
│ - request.client.host    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Check Rate Limit                 │
│ - Endpoint: LOGIN                │
│ - Limit: 5 requests/minute       │
│ - Current: Count()               │
└────────┬─────────────────────────┘
         │
    ┌────┴‾‾‾───┐
    │            │
    ▼            ▼
  < 5            ≥ 5
  │              │
Allow        BLOCK
│              │
│          Calculate
│          Retry-After
│          │
│          ▼
│         Return 429
│         "Too Many
│          Requests"
│
Continue
Process
```

**Development vs Production:**
- **Dev**: In-memory hash map
- **Prod**: Redis recommended
- Configurable per endpoint

---

## 4. Database Schema

```
┌────────────────────────────────────────────────────────────────┐
│                      DATABASE SCHEMA                            │
└────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  auth_user   │◄─────┐
                         ├──────────────┤      │
                         │ id (PK)      │      │
                         │ username     │      │
                         │ email        │      │
                         │ password     │      │
                         │ is_active    │      │
                         │ created_at   │      │
                         └──────────────┘      │
                                               │
        ┌──────────────┬──────────────┬────────┴────────┬──────────────┐
        │              │              │                 │              │
        ▼              ▼              ▼                 ▼              ▼
   ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
   │ Refresh  │  │TokenBlacklist│  │  Login   │  │ Account  │  │Session │
   │ Token    │  │             │  │ Attempt  │  │ Lock     │  │ Log    │
   ├──────────┤  ├─────────────┤  ├──────────┤  ├──────────┤  ├────────┤
   │ id       │  │ id          │  │ id       │  │ id       │  │ id     │
   │ user_id  │  │ token_hash  │  │ user_id  │  │ user_id  │  │ user_id│
   │ token_.. │  │ reason      │  │ email    │  │ lock..   │  │ type   │
   │ revoked_ │  │ created_at  │  │ ip_..    │  │ locked_  │  │ ip_...│
   │    at    │  │ expires_at  │  │ success  │  │ until    │  │ ua     │
   │ expires_ │  │             │  │ created_ │  │ failed.. │  │ status │
   │    at    │  │             │  │    at    │  │ attempt  │  │ detail │
   │ ip_...   │  │             │  │          │  │          │  │ created│
   │ is_active│  │             │  │          │  │          │  │    _at │
   └──────────┘  └─────────────┘  └──────────┘  └──────────┘  └────────┘

KEY INDEXES:
• refresh_tokens: (user_id, is_active), (expires_at)
• token_blacklist: (token_hash), (expires_at)
• login_attempts: (ip_address, created_at), (email, created_at)
• account_locks: (user_id) UNIQUE
• session_logs: (user_id, created_at), (event_type, created_at)
```

---

## 5. Token Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    JWT TOKEN STRUCTURE                          │
└─────────────────────────────────────────────────────────────────┘

ACCESS TOKEN (15 minutes)           REFRESH TOKEN (30 days)
─────────────────────────           ──────────────────────
Header:                             Header:
{                                   {
  "alg": "HS256",                     "alg": "HS256",
  "typ": "JWT"                        "typ": "JWT"
}                                   }

Payload:                            Payload:
{                                   {
  "sub": "123",                       "sub": "123",
  "username": "john_doe",             "username": "john_doe",
  "type": "access",                   "type": "refresh",
  "iat": 1234567890,                  "iat": 1234567890,
  "exp": 1234568790,                  "exp": 1234654290,
  "iss": "ecomm-profit",              "iss": "ecomm-profit",
  "aud": "ecomm-profit-api"           "aud": "ecomm-profit-api"
}                                   }

Signature:                          Signature:
HMACSHA256(                         HMACSHA256(
  base64UrlEncode(header) + "." +   base64UrlEncode(header) + "." +
  base64UrlEncode(payload),        base64UrlEncode(payload),
  secret                           secret
)                                  )
```

---

## 6. Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   HTTPS/TLS Layer 1      │
                    │  - Encryption in transit │
                    │  - Certificate validation │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ CORS Layer 2             │
                    │ - Origin validation      │
                    │ - Preflight checks       │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Rate Limiting Layer 3    │
                    │ - Per IP                 │
                    │ - Per endpoint           │
                    │ - Per user               │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Authentication Layer 4   │
                    │ - Verify JWT sig         │
                    │ - Check expiry           │
                    │ - Validate claims        │
                    │ - Check blacklist        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Authorization Layer 5    │
                    │ - User permissions       │
                    │ - Role-based access      │
                    │ - Resource ownership     │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Business Logic Layer 6   │
                    │ - Process request        │
                    │ - Validate input         │
                    │ - Update database        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Audit & Logging Layer 7  │
                    │ - Log events             │
                    │ - Track changes          │
                    │ - Security monitoring    │
                    └──────────────────────────┘
```

---

## 7. File Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── auth.py                      ✨ NEW: Updated with new functions
│   ├── token_manager.py             ✨ NEW: Core token logic
│   ├── auth_utils.py                ✨ NEW: Security utilities
│   ├── auth_endpoints.py            ✨ NEW: Secure endpoints
│   ├── security_middleware.py       ✨ NEW: FastAPI middleware
│   ├── router.py                    📝 MODIFIED: Added new endpoints
│   └── ...
├── users/
│   ├── models.py                    📝 MODIFIED: UserProfile
│   ├── auth_models.py               ✨ NEW: Auth models
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_secure_auth_models.py ✨ NEW: Auth tables
│   └── ...
├── core/
│   ├── settings.py                  📝 MODIFIED: JWT + security config
│   └── ...
├── logs/                            📁 NEW: Log directory
├── .env.example                     ✨ NEW: Environment template
├── AUTHENTICATION_GUIDE.md          ✨ NEW: Complete guide
├── API_REFERENCE.md                 ✨ NEW: API docs
├── DEPLOYMENT_GUIDE.md              ✨ NEW: Deployment guide
├── README_SECURE_AUTH.md            ✨ NEW: Master reference
├── ARCHITECTURE.md                  ✨ NEW: This file
├── test_auth_system.py              ✨ NEW: Testing script
├── requirements.txt                 📝 MODIFIED: Added dependencies
└── ...

✨ NEW: 8 new files created
📝 MODIFIED: 3 existing files updated
📁 NEW: 1 directory added
```

---

## 8. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│            COMPONENT INTERACTION DIAGRAM                     │
└──────────────────────────────────────────────────────────────┘

CLIENT APP
   │
   ├─ (1) POST /auth/login ──────────┐
   │                                 │
   │◄─ (2) Returns tokens ───────────┤
   │                                 │
   │─ (3) GET /api/users/profile ───┐│
   │      + Authorization header    ││
   │                                 ││
   │◄─ (4) Returns user data ────────┤│
   │                                 ││
   │─ (5) POST /auth/refresh ──────┐│││
   │      + refresh_token         ││││
   │                                 ││││
   │◄─ (6) New tokens ──────────────┘│││
   │                                   ││
   │─ (7) POST /auth/logout ───────┐│││
   │      + refresh_token         ││││
   │                                   ││││
   │◄─ (8) Success ──────────────────┘───┘

                    ▼ (1)
           ┌────────────────────┐
           │   FastAPI Router   │───┐
           └────────┬───────────┘   │
                    │          (9) Middleware Chain
                    ▼          - SecurityHeadersMiddleware
        ┌────────────────────────────┐ - RateLimitMiddleware
        │  auth_endpoints.py         │ - ErrorHandlingMiddleware
        │  ├─ signup()               │
        │  ├─ login()                │
        │  ├─ refresh()              │
        │  └─ logout()               │
        └────────┬───────────────────┘
                 │
        ┌────────▼──────────────────┐
        │ auth.py                    │
        │ ├─ get_current_user()      │
        │ └─ get_current_user_opt()  │
        └────────┬──────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ token_   │ │ auth_    │ │ Django   │
  │ manager  │ │ utils    │ │ Auth     │
  └────┬─────┘ └─────┬────┘ └────┬─────┘
       │             │            │
       ▼             ▼            ▼
  ┌──────────────────────────────────┐
  │      Database (PostgreSQL)        │
  │  ├─ auth_user                     │
  │  ├─ refresh_tokens                │
  │  ├─ token_blacklist               │
  │  ├─ login_attempts                │
  │  ├─ account_locks                 │
  │  └─ session_logs                  │
  └──────────────────────────────────┘
```

---

This completes the comprehensive architecture documentation.

*For implementation details, see individual source files.*
*For deployment, see DEPLOYMENT_GUIDE.md*
*For API usage, see API_REFERENCE.md*
