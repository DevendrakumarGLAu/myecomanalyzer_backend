# API Reference - Secure Authentication Endpoints

## Base URL
```
http://localhost:8000/api/v1/auth
```

---

## 1. User Signup (Registration)

### Endpoint
```
POST /signup
```

### Description
Register a new user with email, username, and password.

### Request Headers
```
Content-Type: application/json
```

### Request Body
```json
{
    "email": "user@example.com",
    "username": "john_doe",
    "password": "MySecurePass123!",
    "password_confirm": "MySecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Field Validation
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| email | string | Yes | Valid email format, unique |
| username | string | Yes | 3-150 chars, alphanumeric, unique |
| password | string | Yes | 8+ chars, upper, digit, special char |
| password_confirm | string | Yes | Must match password |
| first_name | string | No | Max 150 chars |
| last_name | string | No | Max 150 chars |

### Success Response (200)
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user_id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Error Responses

**400 - Bad Request**
```json
{
    "detail": "Email already registered"
}
```

**400 - Validation Error**
```json
{
    "detail": "Password must contain at least one uppercase letter"
}
```

**429 - Too Many Requests**
```json
{
    "detail": "Too many signups from this IP. Try again in 3234 seconds"
}
```

**500 - Server Error**
```json
{
    "detail": "Registration failed"
}
```

---

## 2. User Login

### Endpoint
```
POST /login
```

### Description
Authenticate user and receive JWT tokens.

### Request Headers
```
Content-Type: application/json
```

### Request Body
```json
{
    "email": "user@example.com",
    "password": "MySecurePass123!",
    "device_id": "uuid-123-456",
    "remember_me": false
}
```

### Field Validation
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| email | string | Yes | Must exist and be active |
| password | string | Yes | Correct password required |
| device_id | string | No | For tracking device usage |
| remember_me | boolean | No | For future extended sessions |

### Success Response (200)
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user_id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Error Responses

**401 - Unauthorized**
```json
{
    "detail": "Invalid credentials"
}
```
*Generic message to prevent user enumeration*

**403 - Forbidden (Account Inactive)**
```json
{
    "detail": "Invalid credentials"
}
```

**403 - Forbidden (Account Locked)**
```json
{
    "detail": "Account locked due to multiple failed attempts. Try again in 25 minutes"
}
```

**429 - Rate Limited**
```json
{
    "detail": "Too many attempts. Try again in 45 seconds"
}
```

### Rate Limits
- **Per IP**: 5 attempts per minute
- **Per Email**: 5 attempts per minute
- **Account Lock**: After 5 failed attempts within 15 minutes, lock for 30 minutes

### Security Notes
- Failed attempts are logged with IP and timestamp
- Account automatically locks after multiple failures
- Generic error message to prevent user enumeration
- Constant-time password comparison used

---

## 3. Refresh Token

### Endpoint
```
POST /refresh
```

### Description
Rotate refresh token and get new access token.

### Request Headers
```
Content-Type: application/json
```

### Request Body
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "device_id": "uuid-123-456"
}
```

### Success Response (200)
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900
}
```

### Error Responses

**401 - Invalid Token**
```json
{
    "detail": "Invalid token"
}
```

**403 - Token Reuse Detected**
```json
{
    "detail": "Token reuse detected. Please login again for security."
}
```
*Indicates possible token compromise*

**404 - User Not Found**
```json
{
    "detail": "User not found"
}
```

**429 - Rate Limited**
```json
{
    "detail": "Too many requests from this IP. Try again in 45 seconds"
}
```

### Security Features
- Old refresh token automatically revoked
- Token reuse detection enabled
- Rate limited to prevent abuse
- Each refresh issues new token (rotation)

---

## 4. Logout

### Endpoint
```
POST /logout
```

### Description
Invalidate refresh token and end session.

### Request Headers
```
Authorization: Bearer <access-token>
Content-Type: application/json
```

### Request Body
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Success Response (200)
```json
{
    "message": "Logout successful"
}
```

### Error Responses

**500 - Server Error**
```json
{
    "message": "Logout successful"
}
```
*Note: Always returns success to prevent info leakage*

### Security Notes
- Refresh token is revoked in database
- Token added to blacklist
- Access token can still be used briefly (expiry-based invalidation)
- Session logged for audit trail

---

## 5. Health Check

### Endpoint
```
GET /health
```

### Description
Check if authentication service is operational.

### Success Response (200)
```json
{
    "status": "healthy",
    "timestamp": "2024-05-02T10:30:45.123456"
}
```

---

## Protected Route Example

### Endpoint
```
GET /api/users/profile
```

### Request Headers
```
Authorization: Bearer <access-token>
```

### Success Response (200)
```json
{
    "user_id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Error Responses

**401 - Missing Token**
```json
{
    "detail": "Invalid authorization header format"
}
```

**401 - Invalid Token**
```json
{
    "detail": "Invalid or expired token"
}
```

**403 - User Inactive**
```json
{
    "detail": "User account is inactive"
}
```

**404 - User Not Found**
```json
{
    "detail": "User not found"
}
```

---

## Token Format

### Access Token Payload
```json
{
    "sub": "123",
    "username": "john_doe",
    "type": "access",
    "iat": 1234567890,
    "exp": 1234568790,
    "iss": "ecomm-profit",
    "aud": "ecomm-profit-api"
}
```

### Refresh Token Payload
```json
{
    "sub": "123",
    "username": "john_doe",
    "type": "refresh",
    "iat": 1234567890,
    "exp": 1234654290,
    "iss": "ecomm-profit",
    "aud": "ecomm-profit-api"
}
```

---

## HTTP Status Codes

| Code | Meaning | Common Cause |
|------|---------|-------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input/validation error |
| 401 | Unauthorized | Invalid credentials or token |
| 403 | Forbidden | Account locked or inactive |
| 404 | Not Found | User not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

---

## Error Response Format

All error responses follow this format:
```json
{
    "detail": "error message"
}
```

---

## Authentication Header Format

```
Authorization: Bearer <token>
```

**Example:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJuYW1lIjoiSm9obiBEb2UifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

---

## Response Headers

All responses include:
```
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## Rate Limiting Headers

When rate limited, responses include:
```
Retry-After: 45
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

---

## CORS Headers

Requires proper CORS origin. Add to request:
```
Origin: http://localhost:4200
```

---

## Common cURL Examples

### Sign Up
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "MySecurePass123!"
  }'
```

### Use Access Token
```bash
curl -X GET http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer <access-token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh-token>"
  }'
```

### Logout
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh-token>"
  }'
```

---

## Pagination (Future)

List endpoints will support pagination:
```
GET /api/v1/auth/events?page=1&limit=10
```

Response headers:
```
X-Total-Count: 342
X-Page-Number: 1
```

---

## Filtering (Future)

Audit endpoints will support filtering:
```
GET /api/v1/auth/logs?user_id=1&event_type=login&date_from=2024-01-01
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-05-02 | Initial release |

---

**Last Updated**: May 2, 2024
**API Version**: 1.0
