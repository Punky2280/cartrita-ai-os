"""
CSP Violation Reporting Endpoint for Cartrita AI OS
Handles Content Security Policy violation reports for security monitoring.
"""

import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import Response
import structlog

# Import CSP security config
from services.shared.config.csp_security import csp_config

logger = structlog.get_logger(__name__)

# Create router for CSP endpoints
csp_router = APIRouter(prefix="/api/security", tags=["security"])


@csp_router.post("/csp-violation")
async def handle_csp_violation(
    request: Request, background_tasks: BackgroundTasks
) -> Response:
    """
    Handle CSP violation reports from browsers.

    This endpoint receives violation reports when CSP policies are violated,
    allowing us to monitor potential XSS attacks and policy misconfigurations.
    """
    try:
        # Parse violation report
        report_data = await request.json()

        # Validate report structure
        if not csp_config.is_violation_report_valid(report_data):
            logger.warning(
                "Invalid CSP violation report received", client_ip=request.client.host
            )
            raise HTTPException(status_code=400, detail="Invalid report format")

        # Extract violation details
        csp_report = report_data.get("csp-report", {})
        violation_details = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "document_uri": csp_report.get("document-uri", ""),
            "violated_directive": csp_report.get("violated-directive", ""),
            "blocked_uri": csp_report.get("blocked-uri", ""),
            "original_policy": csp_report.get("original-policy", ""),
            "referrer": csp_report.get("referrer", ""),
            "status_code": csp_report.get("status-code", ""),
            "script_sample": csp_report.get("script-sample", ""),
        }

        # Log violation for monitoring
        logger.warning("CSP violation detected", **violation_details)

        # Process violation in background to avoid blocking response
        background_tasks.add_task(process_csp_violation, violation_details)

        # Return 204 No Content as per CSP spec
        return Response(status_code=204)

    except json.JSONDecodeError:
        logger.warning(
            "Invalid JSON in CSP violation report", client_ip=request.client.host
        )
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(
            "Error processing CSP violation report",
            error=str(e),
            client_ip=request.client.host,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_csp_violation(violation_details: Dict[str, Any]) -> None:
    """
    Process CSP violation in background.

    This function analyzes the violation and can trigger alerts for suspicious activity.
    """
    try:
        # Extract key violation info
        violated_directive = violation_details.get("violated_directive", "")
        blocked_uri = violation_details.get("blocked_uri", "")
        document_uri = violation_details.get("document_uri", "")

        # Analyze violation severity
        severity = analyze_violation_severity(violated_directive, blocked_uri)

        # Log processed violation
        logger.info(
            "CSP violation processed",
            severity=severity,
            directive=violated_directive,
            blocked_uri=blocked_uri,
            document_uri=document_uri,
        )

        # For high-severity violations, could trigger additional actions:
        # - Send alert to security team
        # - Temporarily block IP if pattern detected
        # - Update CSP policy if legitimate resource
        if severity == "high":
            logger.critical(
                "High-severity CSP violation detected - potential XSS attack",
                **violation_details
            )
            # Could implement alerting here

    except Exception as e:
        logger.error("Error in background CSP violation processing", error=str(e))


def analyze_violation_severity(directive: str, blocked_uri: str) -> str:
    """
    Analyze CSP violation to determine severity level.

    Args:
        directive: The violated CSP directive
        blocked_uri: The URI that was blocked

    Returns:
        Severity level: "low", "medium", or "high"
    """
    # High severity indicators
    high_severity_patterns = [
        "javascript:",
        "data:application/javascript",
        "eval",
        "<script",
        "onload=",
        "onclick=",
        "onerror=",
    ]

    # Medium severity directives
    medium_severity_directives = ["script-src", "object-src", "frame-src"]

    # Check for high-severity patterns
    for pattern in high_severity_patterns:
        if pattern.lower() in blocked_uri.lower():
            return "high"

    # Check directive severity
    if any(medium_dir in directive for medium_dir in medium_severity_directives):
        return "medium"

    return "low"


@csp_router.get("/csp-report-stats")
async def get_csp_report_stats() -> Dict[str, Any]:
    """
    Get CSP violation statistics (for monitoring dashboard).

    Note: This would typically connect to a database or monitoring system
    to provide real statistics. For now, returns basic info.
    """
    return {
        "status": "active",
        "report_endpoint": "/api/security/csp-violation",
        "policy_version": "2025.1",
        "nonce_enabled": True,
        "monitoring": "active",
    }


def get_csp_router() -> APIRouter:
    """Get the CSP router for inclusion in FastAPI app."""
    return csp_router
