"""
Orchestration for a single monitoring run.

This module ties together:
- loading API configurations from DynamoDB
- running health checks
- detecting state changes
- updating DynamoDB and sending SNS alerts
"""

from datetime import datetime, timezone

from .dynamodb_client import (
    fetch_all_api_configs,
    get_api_health_state,
    put_api_health_state,
)
from .health_checker import check_api
from .models import ApiHealthState
from .sns_client import send_alert


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _build_alert_subject(api_id: str, old_state: str | None, new_state: str) -> str:
    if old_state is None:
        return f"[API Health] {api_id} is {new_state}"
    return f"[API Health] {api_id} changed from {old_state} to {new_state}"


def _build_alert_message(
    api_id: str,
    url: str,
    old_state: str | None,
    new_state: str,
    status_code: int | None,
    latency_ms: int | None,
    error: str | None,
) -> str:
    lines = [
        f"API ID: {api_id}",
        f"URL: {url}",
        f"Previous state: {old_state or 'UNKNOWN'}",
        f"Current state: {new_state}",
    ]

    if status_code is not None:
        lines.append(f"HTTP status code: {status_code}")
    if latency_ms is not None:
        lines.append(f"Latency (ms): {latency_ms}")
    if error:
        lines.append(f"Error: {error}")

    lines.append(f"Checked at (UTC): {_now_iso()}")
    return "\n".join(lines)


def run_monitor_once() -> None:
    """
    Perform a single monitoring pass.

    This function is designed to be called by a cron job on the EC2
    instance. It keeps the logic small and straightforward on purpose.
    """
    configs = fetch_all_api_configs()

    for config in configs:
        state, status_code, latency_ms, error = check_api(config)

        previous_state_obj = get_api_health_state(config.api_id)
        previous_state = previous_state_obj.last_state if previous_state_obj else None

        now = _now_iso()
        changed = previous_state is None or previous_state != state

        if changed:
            # Only send an alert when the state changes.
            subject = _build_alert_subject(config.api_id, previous_state, state)
            message = _build_alert_message(
                api_id=config.api_id,
                url=config.url,
                old_state=previous_state,
                new_state=state,
                status_code=status_code,
                latency_ms=latency_ms,
                error=error,
            )
            send_alert(subject=subject, message=message)

        # Always store the latest state so next run can compare.
        health_state = ApiHealthState(
            api_id=config.api_id,
            last_state=state,
            last_status_code=status_code,
            last_latency_ms=latency_ms,
            last_checked_at=now,
            last_changed_at=now if changed else (previous_state_obj.last_changed_at if previous_state_obj else now),
            last_error=error,
        )
        put_api_health_state(health_state)
