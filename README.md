# Server — Django REST API

A production-ready REST API built with Django 5.1 and Django REST Framework. Provides user authentication, profile management, virtual wallet, and password reset functionality with JWT-based security.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Database Design](#database-design)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Request & Response Format](#request--response-format)
- [Middleware](#middleware)
- [Email Service](#email-service)
- [Media Files](#media-files)
- [Swagger Documentation](#swagger-documentation)
- [Testing in Postman](#testing-in-postman)

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| Django | 5.1 | Web framework |
| Django REST Framework | Latest | API layer |
| SimpleJWT | Latest | JWT authentication |
| drf-yasg | Latest | Swagger documentation |
| python-dotenv | Latest | Environment variables |
| Pillow | Latest | Image handling |
| SQLite | Built-in | Database |

---

## Project Structure

```
server/
├── server/                     # Django project config
│   ├── settings.py             # All project settings
│   ├── urls.py                 # Root URL configuration
│   ├── middleware.py           # Request logging middleware
│   └── wsgi.py                 # WSGI entry point
├── accounts/                   # Main application
│   ├── migrations/             # Database migrations
│   ├── models.py               # User, VirtualWallet, PasswordResetToken
│   ├── serializers.py          # Request validation & response shaping
│   ├── views.py                # API view logic
│   ├── urls.py                 # App-level URL routing
│   ├── admin.py                # Django admin configuration
│   └── utils.py                # Helpers: api_response, email functions
├── media/                      # Uploaded files (profile images)
│   └── profile_images/
├── .env                        # Environment variables (never commit)
├── server.log                  # Auto-generated request logs
├── db.sqlite3                  # SQLite database
├── manage.py
└── requirements.txt
```

---

## Architecture Overview

```
Incoming Request
       │
       ▼
RequestLogMiddleware        ← logs method, path, status, response time
       │
       ▼
URL Router (server/urls.py)
       │
       ▼
APIView (accounts/views.py)
       │
       ├── CustomTokenAuthentication   ← validates JWT from Authorization header
       ├── Serializer validation       ← validates & sanitizes input
       ├── Business logic              ← create user, send email, update profile
       └── api_response()             ← unified { status, message, data } format
```

---

## Database Design

Three tables with single responsibility separation:

### `accounts_user`
Core identity table. Extends Django's `AbstractBaseUser` to use `email` as the login field instead of `username`.

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| email | EmailField | Unique, used for login |
| full_name | CharField | Display name |
| age | PositiveIntegerField | Optional |
| father_name | CharField | Optional |
| profile_image | ImageField | Stored in `media/profile_images/` |
| is_active | BooleanField | Default True |
| is_staff | BooleanField | Admin access |
| created_at | DateTimeField | Auto timestamp |

### `accounts_virtualwallet`
Auto-created for every user at signup. Kept separate from User to maintain clean separation of concerns and allow future extension (transactions, multi-currency, history).

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| user | OneToOneField | Links to User |
| balance | DecimalField | Default 0.00 (not Float — avoids floating point precision loss) |
| currency | CharField | Default USD |
| created_at | DateTimeField | Auto timestamp |

### `accounts_passwordresettoken`
Stores temporary single-use tokens for password reset flow. Kept separate from User because tokens are events, not permanent user properties. Allows multiple reset requests without overwriting previous ones.

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| user | ForeignKey | Links to User |
| token | UUIDField | UUID4, unique, emailed to user |
| is_used | BooleanField | Marked True after use, prevents reuse |
| created_at | DateTimeField | Can be used to implement expiry |

> **Why 3 tables and not 1?** Each table has one responsibility. Mixing wallet and token data into the User row would make the table hard to maintain, violate single responsibility principle, and prevent clean scaling.

---

## Getting Started

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd server

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create superuser (for admin panel)

```bash
python manage.py createsuperuser
```

### 6. Start server

```bash
python manage.py runserver
```

---

## Environment Variables

Create a `.env` file in the project root. Never commit this file.

```env
SECRET_KEY=your-secret-key-minimum-50-characters-long
DEBUG=True

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your@email.com

ACCESS_TOKEN_LIFETIME_MINUTES=30
REFRESH_TOKEN_LIFETIME_DAYS=1
```

Generate a secure SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

> **Note:** `SECRET_KEY` must be at least 32 characters. Short keys cause JWT `InsecureKeyLengthWarning` and weaker token signing.

---

## API Endpoints

Base URL: `http://127.0.0.1:8000`

### Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| POST | `/api/auth/signup/` | No | Register new user |
| POST | `/api/auth/login/` | No | Login, returns JWT tokens |
| POST | `/api/auth/forgot-password/` | No | Send reset token to email |
| POST | `/api/auth/reset-password/` | No | Reset password using token |
| GET | `/api/auth/profile/` | Yes (JWT) | Get authenticated user profile |
| PATCH | `/api/auth/profile/update/` | Yes (JWT) | Update profile fields |

### Other

| URL | Description |
|---|---|
| `/swagger/` | Swagger UI — interactive API docs |
| `/redoc/` | ReDoc — alternative API docs |
| `/admin/` | Django admin panel |

---

## Authentication

This API uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`.

### Flow

```
POST /api/auth/login/
→ Returns access token + refresh token

Use access token in Authorization header for protected endpoints:
Authorization: Bearer <access_token>
```

### Token Lifetime

| Token | Default Lifetime | Configurable via |
|---|---|---|
| Access | 30 minutes | `ACCESS_TOKEN_LIFETIME_MINUTES` in `.env` |
| Refresh | 1 day | `REFRESH_TOKEN_LIFETIME_DAYS` in `.env` |

### JWT Payload

The access token contains:

```json
{
  "user_id": "1",
  "email": "user@example.com",
  "full_name": "John Doe",
  "age": 25,
  "father_name": "James Doe"
}
```

### Custom Token Authentication

`GetProfileView` and `UpdateProfileView` use a custom `CustomTokenAuthentication` class that accepts tokens in any of these formats:

```
Authorization: eyJhbGci...                 ← raw token
Authorization: Bearer eyJhbGci...          ← with Bearer prefix
Authorization: Token eyJhbGci...           ← with Token prefix
```

---

## Request & Response Format

All endpoints return a unified response structure:

```json
{
    "status": "success",
    "message": "Human-readable message here.",
    "data": {}
}
```

### Success Example

```json
{
    "status": "success",
    "message": "Account created successfully.",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "age": 22,
        "father_name": "James Doe",
        "profile_image": "/media/profile_images/photo.jpg",
        "created_at": "2026-05-14T10:00:00Z",
        "wallet_balance": "0.00"
    }
}
```

### Error Example

```json
{
    "status": "error",
    "message": "Email already exists.",
    "data": {}
}
```

---

## Middleware

### `RequestLogMiddleware`

Logs every HTTP request automatically to `server.log` in the project root.

**Log format:**
```
[2026-05-14 17:30:00] POST /api/auth/login/ - 200 - 45.23ms
[2026-05-14 17:30:05] GET /api/auth/profile/ - 200 - 12.11ms
[2026-05-14 17:30:10] PATCH /api/auth/profile/update/ - 400 - 8.50ms
```

**What is logged:**
- Timestamp
- HTTP method
- Request path
- Response status code
- Response time in milliseconds

The log file is auto-created on first request. No manual setup needed.

---

## Email Service

Emails are sent via SMTP using Django's built-in `send_mail`. Configured to work with any SMTP provider (Gmail, Postmark, SendGrid, etc.).

### Emails Sent

| Trigger | Subject | Content |
|---|---|---|
| Signup | Welcome to Server App! | Welcome message + wallet creation confirmation |
| Forgot Password | Password Reset Request | UUID reset token, single-use warning |

### Configuration

Set SMTP credentials in `.env`. For Gmail, use an App Password (not your regular password). For Postmark, use `smtp.postmarkapp.com` with your server token as the password.

---

## Media Files

Profile images uploaded during signup or profile update are stored in:

```
media/
└── profile_images/
    └── <filename>.<ext>
```

Accessible via: `http://127.0.0.1:8000/media/profile_images/<filename>`

### Old Image Cleanup

When a user uploads a new profile image via the update endpoint, the old image is automatically deleted from disk before saving the new one. This prevents orphaned files accumulating in the media folder.

---

## Swagger Documentation

Interactive API documentation available at:

```
http://127.0.0.1:8000/swagger/
```

### How to authenticate in Swagger

1. Call `POST /api/auth/login/` to get your access token
2. Click **Authorize** button (top right)
3. Enter your token in the `Authorization` field
4. Click **Authorize** → **Close**
5. All subsequent requests will include your token automatically

---

### Endpoint Reference

| Endpoint | Method | Body Type | Auth |
|---|---|---|---|
| `/api/auth/signup/` | POST | form-data | No |
| `/api/auth/login/` | POST | raw JSON | No |
| `/api/auth/forgot-password/` | POST | raw JSON | No |
| `/api/auth/reset-password/` | POST | raw JSON | No |
| `/api/auth/profile/` | GET | none | Bearer Token |
| `/api/auth/profile/update/` | PATCH | form-data | Bearer Token |

> Use **form-data** for any endpoint that accepts a profile image. Use **raw JSON** for all others.

---

## Admin Panel

Access at `http://127.0.0.1:8000/admin/` with your superuser credentials.

The admin panel shows each user with their virtual wallet details inline — open any user record to see their wallet balance, currency, and creation date directly on the same page.

---

## Security Notes

- CSRF middleware is intentionally disabled — JWT in the Authorization header is stateless and not vulnerable to CSRF attacks
- `SessionAuthentication` is not used — only `JWTAuthentication`
- Secret key must be at least 32 characters for secure JWT signing
- `.env` file must never be committed to version control — add it to `.gitignore`