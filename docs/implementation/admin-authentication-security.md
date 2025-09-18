# Admin Authentication Security Implementation

## Overview

This document describes the comprehensive admin authentication security implementation for Cartrita AI OS. The system provides JWT-based role-based access control (RBAC) for administrative functions with comprehensive audit logging and security hardening.

## Security Features

### 🔐 Authentication Methods

1. **JWT-Based Authentication (Primary)**
   - Bearer token authentication with role-based permissions
   - Secure token validation with expiration
   - Integration with existing JWT infrastructure

2. **API Key Authentication (Legacy Fallback)**
   - Admin-specific API key for backwards compatibility
   - Environment-configured admin key validation
   - Gradual migration path to JWT-only authentication

### 🛡️ Role-Based Access Control (RBAC)

#### Admin Permission Levels

| Level | Permissions | Use Case |
|-------|------------|----------|
| **Super Admin** | `admin:*`, `admin:system_shutdown`, `admin:security_config` | Full system control, user management |
| **Admin** | `admin:reload_agents`, `admin:system_stats`, `admin:user_management` | Operational management |
| **Operator** | `admin:system_stats` | Read-only monitoring |

#### Permission Structure

```
admin:*                    # Super admin wildcard
admin:reload_agents        # Agent management
admin:system_stats        # System monitoring
admin:user_management      # User administration
admin:security_config     # Security settings
admin:system_shutdown     # System control
```

### 📊 Audit Logging

All admin actions are comprehensively logged with:

- **User identification** (user_id, admin_level)
- **Action details** (action, permissions required)
- **Client information** (IP address, user agent)
- **Success/failure status** and error details
- **Timestamp** and additional metadata

## Implementation Architecture

### Core Components

1. **`AdminUser` Model**
   ```python
   class AdminUser(BaseModel):
       user_id: str
       permissions: Set[str]
       is_admin: bool
       admin_level: str
       last_login: Optional[datetime]
   ```

2. **`AdminAuthConfig` Service**
   - Permission level configuration
   - Admin user whitelist management
   - Audit log collection and storage
   - Permission validation logic

3. **Authentication Dependencies**
   ```python
   # Permission-specific access control
   @Depends(require_admin_permission("admin:reload_agents"))

   # Level-based access control
   @Depends(require_super_admin)
   @Depends(require_any_admin)
   ```

### Integration Points

#### JWT Authentication Integration

The admin auth system integrates with the existing JWT infrastructure:

```python
from cartrita.orchestrator.services.jwt_auth import (
    get_current_user,  # Base JWT validation
    TokenData,         # User token information
    jwt_manager        # Token creation/validation
)
```

#### FastAPI Endpoint Security

Admin endpoints are secured using dependency injection:

```python
@app.post("/api/admin/reload-agents")
async def reload_agents(
    admin_user: AdminUser = Depends(require_admin_permission("admin:reload_agents"))
):
    # Admin action with automatic audit logging
    logger.info("Agents reloaded by admin", admin_user=admin_user.user_id)
    await supervisor.reload_agents()
    return {"message": "Agents reloaded successfully"}
```

## Security Configuration

### Environment Variables

```bash
# Admin Users (comma-separated)
ADMIN_USERS=cartrita_super_admin,admin_user,system_admin

# Super Admin (highest privilege)
SUPER_ADMIN_USER=cartrita_super_admin

# Admin API Key (legacy compatibility)
ADMIN_API_KEY=secure-admin-key-2025-change-in-production

# Security Settings
ADMIN_REQUIRE_HTTPS=true
ADMIN_AUDIT_LOGGING_ENABLED=true
ADMIN_RATE_LIMIT_ENABLED=true
ADMIN_ALLOWED_IPS=127.0.0.1/32,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```

### Production Security Hardening

1. **HTTPS Enforcement**
   - Set `ADMIN_REQUIRE_HTTPS=true`
   - Use TLS 1.2+ for all admin endpoints

2. **IP Restrictions**
   - Configure `ADMIN_ALLOWED_IPS` with specific networks
   - Avoid wildcard (`0.0.0.0/0`) access

3. **Strong Credentials**
   - Use ≥32 character admin API keys
   - Regular credential rotation policy
   - Consider hardware security modules (HSM)

4. **Audit Logging**
   - Enable comprehensive logging (`ADMIN_AUDIT_LOGGING_ENABLED=true`)
   - Configure log retention (90+ days)
   - Set up log monitoring and alerting

## API Endpoints

### Admin Endpoints

| Endpoint | Method | Permission Required | Description |
|----------|--------|-------------------|-------------|
| `/api/admin/reload-agents` | POST | `admin:reload_agents` | Reload all agent configurations |
| `/api/admin/stats` | GET | `admin:system_stats` | Get system statistics |
| `/api/admin/audit-logs` | GET | `admin:system_stats` | Get admin audit logs |
| `/api/admin/create-admin-token` | POST | Super Admin Only | Create admin JWT tokens |
| `/api/admin/health` | GET | Any Admin Level | Admin authentication health check |

### Authentication Headers

#### JWT Authentication (Primary)
```bash
Authorization: Bearer <jwt-token>
```

#### API Key Authentication (Fallback)
```bash
X-Admin-API-Key: <admin-api-key>
# or
X-API-Key: <admin-api-key>
```

## Usage Examples

### Creating Admin Tokens

```python
from cartrita.orchestrator.services.admin_auth import create_admin_token

# Create admin token
admin_token = create_admin_token('admin_user', 'admin')

# Create super admin token
super_token = create_admin_token('super_admin_user', 'super_admin')

# Create operator token
operator_token = create_admin_token('operator_user', 'operator')
```

### Securing Custom Admin Endpoints

```python
@app.post("/api/admin/custom-action")
async def custom_admin_action(
    admin_user: AdminUser = Depends(require_admin_permission("admin:custom_action"))
):
    # Automatic authentication and authorization
    # Automatic audit logging
    return {"message": "Custom action completed"}
```

### Checking Admin Permissions

```python
from cartrita.orchestrator.services.admin_auth import admin_config

# Check if user has admin permissions
has_permission = admin_config.validate_admin_permission(
    admin_user,
    "admin:reload_agents"
)

# Get admin level for user
admin_level = admin_config.get_admin_level(
    user_id,
    user_permissions
)
```

## Testing and Validation

### Security Validation Script

Run comprehensive security validation:

```bash
python scripts/validate_admin_auth.py
```

The validation script checks:
- ✅ Environment configuration
- ✅ Permission hierarchy
- ✅ JWT integration
- ✅ Audit logging functionality
- ✅ Access control mechanisms
- ✅ Security hardening measures

### Unit Tests

```bash
# Run admin authentication tests
pytest tests/test_admin_authentication.py -v

# Run with coverage
pytest tests/test_admin_authentication.py --cov=services.ai_orchestrator.cartrita.orchestrator.services.admin_auth
```

### Integration Testing

```python
# Test full authentication flow
@pytest.mark.integration
async def test_admin_endpoint_access():
    # Create admin token
    admin_token = create_admin_token('test_admin', 'admin')

    # Test endpoint access
    response = await client.post(
        "/api/admin/reload-agents",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
```

## Security Compliance

### OWASP Top 10 Coverage

| OWASP Category | Implementation |
|----------------|---------------|
| **A01: Broken Access Control** | ✅ Role-based admin access control |
| **A02: Cryptographic Failures** | ✅ JWT token security, strong API keys |
| **A05: Security Misconfiguration** | ✅ Secure defaults, configuration validation |
| **A07: Authentication Failures** | ✅ Multi-layer admin authentication |
| **A09: Logging/Monitoring** | ✅ Comprehensive audit logging |

### Security Standards Alignment

- **NIST Cybersecurity Framework**: Identity and Access Management
- **ISO 27001**: Access Control (A.9.1, A.9.2)
- **SOC 2 Type II**: Logical Access Controls
- **GDPR**: Data Protection with audit trails

## Migration Guide

### From API Key to JWT Authentication

1. **Phase 1: Dual Authentication**
   - Deploy admin authentication system
   - Continue supporting legacy API keys
   - Begin issuing JWT tokens to admin users

2. **Phase 2: JWT Primary**
   - Update admin clients to use JWT tokens
   - Log deprecation warnings for API key usage
   - Monitor adoption metrics

3. **Phase 3: JWT Only**
   - Remove API key fallback authentication
   - Update documentation and examples
   - Complete migration to JWT-only authentication

### Legacy API Key Support

During migration, the system supports both methods:

```python
# JWT Authentication (preferred)
admin_user: AdminUser = Depends(require_admin_permission("admin:reload_agents"))

# API Key Fallback (legacy)
api_key: str = Depends(verify_admin_api_key)
```

## Monitoring and Alerting

### Security Metrics

Monitor these key security indicators:

1. **Authentication Metrics**
   - Failed admin authentication attempts
   - Admin token usage patterns
   - Concurrent admin sessions

2. **Authorization Metrics**
   - Permission denied attempts
   - Admin privilege escalation attempts
   - Unauthorized admin endpoint access

3. **Audit Metrics**
   - Admin action frequency
   - Off-hours admin access
   - Bulk admin operations

### Alert Configuration

Configure alerts for:

```yaml
# Critical Alerts
- Failed admin authentication (>5 attempts/hour)
- Admin access from unauthorized IPs
- Admin privilege escalation attempts
- Bulk admin operations outside business hours

# Warning Alerts
- Admin API key usage (migration reminder)
- Admin access without HTTPS
- Long-running admin sessions
```

## Troubleshooting

### Common Issues

1. **Admin Access Denied**
   ```bash
   # Check admin user configuration
   echo $ADMIN_USERS

   # Verify JWT token
   python -c "from jwt import decode; print(decode('TOKEN', verify=False))"

   # Check audit logs
   curl -H "Authorization: Bearer TOKEN" /api/admin/audit-logs
   ```

2. **Permission Errors**
   ```bash
   # Validate admin permissions
   python scripts/validate_admin_auth.py

   # Check user admin level
   # Look in audit logs for permission validation failures
   ```

3. **JWT Token Issues**
   ```bash
   # Create new admin token
   curl -X POST /api/admin/create-admin-token \
        -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
        -d '{"user_id": "admin_user", "admin_level": "admin"}'
   ```

### Debug Mode

Enable debug logging for admin authentication:

```python
import logging
logging.getLogger('cartrita.admin.security').setLevel(logging.DEBUG)
```

## Roadmap

### Future Enhancements

1. **Multi-Factor Authentication (MFA)**
   - TOTP integration for super admin accounts
   - SMS/Email verification for sensitive operations
   - Hardware token support (YubiKey)

2. **Advanced Audit Features**
   - Real-time admin session monitoring
   - Automated anomaly detection
   - Integration with SIEM systems

3. **Role Management UI**
   - Web-based admin role management
   - Self-service admin token renewal
   - Visual permission matrix

4. **Session Management**
   - Admin session timeout controls
   - Concurrent session limits
   - Remote session termination

## Support and Documentation

- **Implementation Guide**: This document
- **API Reference**: `/docs` endpoint with admin authentication
- **Security Validation**: `scripts/validate_admin_auth.py`
- **Test Suite**: `tests/test_admin_authentication.py`
- **Configuration Examples**: `.env.admin.example`

## Changelog

### Version 1.0.0 (Current)
- ✅ JWT-based admin authentication
- ✅ Role-based permission system
- ✅ Comprehensive audit logging
- ✅ Security validation framework
- ✅ Migration support for API keys
- ✅ Production security hardening

---

**Security Contact**: security@cartrita.ai
**Documentation Version**: 1.0.0
**Last Updated**: January 2025
