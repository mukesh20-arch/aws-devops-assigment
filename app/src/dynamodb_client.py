"""
DynamoDB client helpers for the API Health Monitoring System.

This module keeps the database access logic in one place so that the rest
of the code can just work with Python objects.
"""

from typing import List, Optional

import boto3

from .config import get_config
from .models import ApiConfig, ApiHealthState


def _get_dynamodb_resource():
    """Create a DynamoDB resource using the AWS region from config."""
    cfg = get_config()
    return boto3.resource("dynamodb", region_name=cfg.aws_region)


def get_config_table():
    """Return a handle to the API configuration table."""
    cfg = get_config()
    dynamodb = _get_dynamodb_resource()
    return dynamodb.Table(cfg.dynamodb_config_table)


def get_state_table():
    """Return a handle to the API health state table."""
    cfg = get_config()
    dynamodb = _get_dynamodb_resource()
    return dynamodb.Table(cfg.dynamodb_state_table)


def fetch_all_api_configs() -> List[ApiConfig]:
    """
    Read all API configurations from DynamoDB.

    For an intern-level project we can keep it simple and just scan the
    table. If the number of APIs grows very large, we could later
    introduce pagination or filtering.
    """
    table = get_config_table()
    response = table.scan()
    items = response.get("Items", [])

    configs: List[ApiConfig] = []
    for item in items:
        configs.append(
            ApiConfig(
                api_id=item["api_id"],
                url=item["url"],
                method=item.get("method", "GET"),
                expected_status_codes=item.get("expected_status_codes", [200]),
                timeout_ms=int(item.get("timeout_ms", 3000)),
                check_interval_seconds=int(item.get("check_interval_seconds", 60)),
                notify_emails=item.get("notify_emails", []),
                enabled=bool(item.get("enabled", True)),
            )
        )

    return configs


def get_api_health_state(api_id: str) -> Optional[ApiHealthState]:
    """Fetch the last known state for a single API, if it exists."""
    table = get_state_table()
    response = table.get_item(Key={"api_id": api_id})
    item = response.get("Item")
    if not item:
        return None

    return ApiHealthState(
        api_id=item["api_id"],
        last_state=item["last_state"],
        last_status_code=item.get("last_status_code"),
        last_latency_ms=item.get("last_latency_ms"),
        last_checked_at=item["last_checked_at"],
        last_changed_at=item.get("last_changed_at"),
        last_error=item.get("last_error"),
    )


def put_api_health_state(state: ApiHealthState) -> None:
    """Store or update the health state for an API."""
    table = get_state_table()
    table.put_item(
        Item={
            "api_id": state.api_id,
            "last_state": state.last_state,
            "last_status_code": state.last_status_code,
            "last_latency_ms": state.last_latency_ms,
            "last_checked_at": state.last_checked_at,
            "last_changed_at": state.last_changed_at,
            "last_error": state.last_error,
        }
    )
