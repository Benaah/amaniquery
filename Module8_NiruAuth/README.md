# Module 8: NiruAuth - Authentication and Authorization System

Comprehensive authentication and authorization system for AmaniQuery, supporting both user accounts and third-party integrations.

## Features

### Authentication Methods
- **User Authentication**: Email/password, session management, password reset
- **API Keys**: Prefix-based keys for integrations and users
- **OAuth 2.0**: Client credentials, authorization code, and refresh token flows
- **JWT Tokens**: Short-lived access tokens with refresh tokens

### Authorization
- **Role-Based Access Control (RBAC)**: User roles (user, admin) and integration roles
- **Permission-Based**: Fine-grained permissions (e.g., `query:read`, `research:write`)
- **Scope-Based**: OAuth scopes and API key scopes
- **Policy Engine**: Time-based, IP-based, and custom policy conditions

### API Gateway Features
- **Rate Limiting**: Token bucket algorithm with per-user/integration/endpoint limits
- **Usage Tracking**: Detailed logging of API calls, token usage, and costs
- **Analytics**: Usage statistics and dashboards

## Installation

1. Run database migration:
```bash
python migrate_auth_db.py
```

2. Set environment variables:
```bash
DATABASE_URL=postgresql://user:password@localhost/amaniquery
JWT_SECRET_KEY=your-secret-key-here
ENABLE_AUTH=true
```

## Usage

### Enable Authentication

Set `ENABLE_AUTH=true` in your environment to enable the auth system.

### User Registration

```python
POST /api/v1/auth/register
{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "name": "John Doe"
}
```

### User Login

```python
POST /api/v1/auth/login
{
    "email": "user@example.com",
    "password": "SecurePassword123"
}
```

Returns a session token that should be included in subsequent requests.

### Using API Keys

```bash
curl -H "X-API-Key: aq_live_..." https://api.example.com/query
```

### Using OAuth 2.0

1. Register a client:
```python
POST /api/v1/auth/oauth/clients
{
    "name": "My App",
    "redirect_uris": ["https://myapp.com/callback"],
    "grant_types": ["authorization_code"]
}
```

2. Get authorization code:
```python
GET /api/v1/auth/oauth/authorize?client_id=...&redirect_uri=...
```

3. Exchange code for token:
```python
POST /api/v1/auth/oauth/token
{
    "grant_type": "authorization_code",
    "client_id": "...",
    "client_secret": "...",
    "code": "..."
}
```

## API Endpoints

### User Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user profile
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/password/change` - Change password
- `POST /api/v1/auth/password/reset-request` - Request password reset
- `POST /api/v1/auth/password/reset` - Reset password

### Admin
- `GET /api/v1/auth/admin/users` - List users
- `GET /api/v1/auth/admin/users/{id}` - Get user
- `PUT /api/v1/auth/admin/users/{id}` - Update user
- `POST /api/v1/auth/admin/users/{id}/roles` - Assign role

### Integrations
- `POST /api/v1/auth/integrations` - Create integration
- `GET /api/v1/auth/integrations` - List integrations
- `GET /api/v1/auth/integrations/{id}` - Get integration
- `PUT /api/v1/auth/integrations/{id}` - Update integration
- `DELETE /api/v1/auth/integrations/{id}` - Delete integration

### API Keys
- `POST /api/v1/auth/integrations/{id}/keys` - Create API key
- `GET /api/v1/auth/integrations/{id}/keys` - List API keys
- `DELETE /api/v1/auth/integrations/{id}/keys/{key_id}` - Revoke key
- `POST /api/v1/auth/integrations/{id}/keys/{key_id}/rotate` - Rotate key

### OAuth
- `POST /api/v1/auth/oauth/clients` - Register client
- `GET /api/v1/auth/oauth/authorize` - Authorization endpoint
- `POST /api/v1/auth/oauth/token` - Token endpoint
- `POST /api/v1/auth/oauth/revoke` - Revoke token

### Analytics
- `GET /api/v1/auth/analytics/integrations/{id}/usage` - Integration usage
- `GET /api/v1/auth/analytics/users/usage` - User usage
- `GET /api/v1/auth/analytics/dashboard` - Admin dashboard

## Protecting Endpoints

Use FastAPI dependencies to protect endpoints:

```python
from Module8_NiruAuth.dependencies import get_current_user, require_permission

@app.get("/protected")
async def protected_endpoint(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user.email}"}

@app.post("/admin-only")
async def admin_endpoint(admin: User = Depends(require_admin)):
    return {"message": "Admin access"}
```

## Configuration

See `Module8_NiruAuth/config.py` for all configuration options including:
- JWT settings
- Rate limits
- Password requirements
- Default roles and permissions

## Security Considerations

- API keys are hashed before storage
- Passwords use bcrypt hashing
- JWT tokens have short expiration times
- Rate limiting prevents abuse
- All auth events are logged

## Future Enhancements

- Two-factor authentication (2FA)
- Social login (Google, GitHub)
- Webhook authentication
- Multi-tenant support
- Usage-based billing integration

