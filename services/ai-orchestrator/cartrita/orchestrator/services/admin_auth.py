# Cartrita AI OS - Admin Authentication Service
# Secure admin-level authentication with role-based access control

"""
Admin Authentication service for Cartrita AI OS.
Provides secure admin-level authentication with proper role validation and audit logging.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Set

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from .jwt_auth import TokenData, get_current_user, jwt_manager

# Configure logging for admin access
admin_logger = logging.getLogger("cartrita.admin.security")
admin_logger.setLevel(logging.INFO)


class AdminUser(BaseModel):
    """Admin user model with role information."""

    user_id: str
    permissions: Set[str]
    is_admin: bool
    admin_level: str  # 'super_admin', 'admin', 'operator'
    last_login: Optional[datetime] = None


class AdminAuthConfig:
    """Configuration for admin authentication."""

    def __init__(self):
        # Required admin permissions
        self.ADMIN_PERMISSIONS = {
            "super_admin": [
                "admin:*",
                "admin:reload_agents",
                "admin:system_stats",
                "admin:user_management",
                "admin:security_config",
                "admin:system_shutdown",
            ],
            "admin": [
                "admin:reload_agents",
                "admin:system_stats",
                "admin:user_management",
            ],
            "operator": ["admin:system_stats"],
        }

        # Admin user whitelist from environment
        admin_users_str = os.getenv("ADMIN_USERS", "")
        self.admin_user_ids = (
            set(admin_users_str.split(",")) if admin_users_str else set()
        )

        # Super admin user (highest level)
        super_admin = os.getenv("SUPER_ADMIN_USER", "cartrita_super_admin")
        if super_admin:
            self.admin_user_ids.add(super_admin)

        # Session tracking (in production, use Redis)
        self._admin_sessions = {}

        # Audit log storage (in production, use persistent storage)
        self._audit_log = []

    def is_admin_user(self, user_id: str) -> bool:
        """Check if user_id is in the admin user list."""
        return user_id in self.admin_user_ids

    def get_admin_level(self, user_id: str, permissions: Set[str]) -> Optional[str]:
        """Determine admin level based on user and permissions."""
        if not self.is_admin_user(user_id):
            return None

        # Check for super admin permissions
        if any(
            perm.startswith("admin:*") or "admin:system_shutdown" in permissions
            for perm in permissions
        ):
            return "super_admin"

        # Check for full admin permissions
        if "admin:user_management" in permissions:
            return "admin"

        # Check for operator permissions
        if "admin:system_stats" in permissions:
            return "operator"

        return None

    def validate_admin_permission(
        self, user: AdminUser, required_permission: str
    ) -> bool:
        """Validate if admin user has required permission."""
        if not user.is_admin:
            return False

        # Super admin has all permissions
        if user.admin_level == "super_admin":
            return True

        # Check specific permission
        return required_permission in user.permissions

    def log_admin_access(
        self,
        admin_user: AdminUser,
        action: str,
        request: Request = None,
        success: bool = True,
        error: Optional[str] = None,
        additional_info: Optional[dict] = None,
    ):
        """Log admin access with comprehensive audit information."""

        log_data = {
            "user_id": admin_user.user_id,
            "admin_level": admin_user.admin_level,
            "action": action,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if request:
            log_data["client_ip"] = request.client.host if request.client else "unknown"
            log_data["user_agent"] = request.headers.get("user-agent", "unknown")

        if error:
            log_data["error"] = error

        if additional_info:
            log_data.update(additional_info)

        # Store audit log
        self._audit_log.append(log_data)

        # Log to structured logger - format log data as string for standard logger
        log_msg_parts = []
        for key, value in log_data.items():
            log_msg_parts.append(f"{key}={value}")
        log_message = f"Admin access {'granted' if success else 'denied'}: {', '.join(log_msg_parts)}"

        if success:
            admin_logger.info(log_message)
        else:
            admin_logger.warning(log_message)

    def get_audit_logs(self, limit: int = 100) -> list:
        """Get recent audit logs."""
        return self._audit_log[-limit:]


# Global admin configuration
admin_config = AdminAuthConfig()


async def get_admin_user(
    request: Request, current_user: TokenData = Depends(get_current_user)
) -> AdminUser:
    """
    Get current admin user with proper validation.
    Raises HTTPException if user is not an admin.
    """
    # Check if user is in admin list
    if not admin_config.is_admin_user(current_user.user_id):
        admin_config.log_admin_access(
            AdminUser(
                user_id=current_user.user_id,
                permissions=set(current_user.permissions),
                is_admin=False,
                admin_level="none",
            ),
            "admin_access_attempt",
            request,
            success=False,
            additional_info={"reason": "not_admin_user"},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin privileges required",
        )

    # Determine admin level
    user_permissions = set(current_user.permissions)
    admin_level = admin_config.get_admin_level(current_user.user_id, user_permissions)

    if not admin_level:
        admin_config.log_admin_access(
            AdminUser(
                user_id=current_user.user_id,
                permissions=user_permissions,
                is_admin=False,
                admin_level="none",
            ),
            "admin_access_attempt",
            request,
            success=False,
            additional_info={"reason": "insufficient_permissions"},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Insufficient admin permissions",
        )

    admin_user = AdminUser(
        user_id=current_user.user_id,
        permissions=user_permissions,
        is_admin=True,
        admin_level=admin_level,
        last_login=datetime.now(timezone.utc),
    )

    return admin_user


async def require_admin_permission(permission: str):
    """Dependency factory for admin permission-based access control."""

    async def admin_permission_checker(
        request: Request, admin_user: AdminUser = Depends(get_admin_user)
    ) -> AdminUser:
        if not admin_config.validate_admin_permission(admin_user, permission):
            admin_config.log_admin_access(
                admin_user,
                f"admin_permission_check:{permission}",
                request,
                success=False,
                additional_info={"required_permission": permission},
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Admin permission required: {permission}",
            )

        # Log successful admin access
        admin_config.log_admin_access(
            admin_user,
            f"admin_permission_granted:{permission}",
            request,
            success=True,
            additional_info={"granted_permission": permission},
        )

        return admin_user

    return admin_permission_checker


# Convenience dependencies for common admin access levels
async def require_super_admin(
    request: Request, admin_user: AdminUser = Depends(get_admin_user)
) -> AdminUser:
    """Require super admin level access."""
    if admin_user.admin_level != "super_admin":
        admin_config.log_admin_access(
            admin_user,
            "super_admin_access_attempt",
            request,
            success=False,
            additional_info={"current_level": admin_user.admin_level},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Super admin privileges required",
        )

    admin_config.log_admin_access(
        admin_user, "super_admin_access_granted", request, success=True
    )

    return admin_user


async def require_any_admin(
    request: Request, admin_user: AdminUser = Depends(get_admin_user)
) -> AdminUser:
    """Require any level of admin access (operator, admin, or super_admin)."""
    admin_config.log_admin_access(
        admin_user,
        "admin_access_granted",
        request,
        success=True,
        additional_info={"admin_level": admin_user.admin_level},
    )

    return admin_user


# Legacy API key admin authentication (for backwards compatibility)
async def verify_admin_api_key(request: Request) -> str:
    """
    Verify admin API key (legacy method).
    This is a fallback for admin endpoints during JWT migration.
    """
    admin_api_key = os.getenv("ADMIN_API_KEY")

    if not admin_api_key:
        # If no admin API key is set, require JWT authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Please use JWT token or configure ADMIN_API_KEY.",
        )

    api_key_header = request.headers.get("X-Admin-API-Key")
    if not api_key_header:
        # Try regular API key header as fallback
        api_key_header = request.headers.get("X-API-Key")

    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )

    if api_key_header != admin_api_key:
        # Log failed admin access attempt
        client_ip = request.client.host if request.client else "unknown"
        admin_logger.warning(
            "Failed admin API key authentication",
            client_ip=client_ip,
            attempted_key=(
                api_key_header[:8] + "..."
                if len(api_key_header) > 8
                else api_key_header
            ),
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin API key"
        )

    # Log successful admin access
    client_ip = request.client.host if request.client else "unknown"
    admin_logger.info(
        "Admin API key authentication successful",
        client_ip=client_ip,
        auth_method="admin_api_key",
    )

    return api_key_header


def create_admin_token(user_id: str, admin_level: str = "admin") -> str:
    """
    Create a JWT token with admin permissions.
    Used for creating admin user tokens.
    """
    if admin_level not in admin_config.ADMIN_PERMISSIONS:
        raise ValueError(f"Invalid admin level: {admin_level}")

    permissions = admin_config.ADMIN_PERMISSIONS[admin_level]
    return jwt_manager.create_access_token(user_id, permissions)


def initialize_default_admin() -> Optional[str]:
    """
    Initialize default admin user if none exist.
    Returns the created admin token or None if admin already exists.
    """
    if admin_config.admin_user_ids:
        return None  # Admin users already configured

    # Create default super admin
    default_admin_id = "cartrita_default_admin"
    admin_config.admin_user_ids.add(default_admin_id)

    # Create super admin token
    token = create_admin_token(default_admin_id, "super_admin")

    admin_logger.info(
        "Default admin user created",
        user_id=default_admin_id,
        admin_level="super_admin",
    )

    return token
