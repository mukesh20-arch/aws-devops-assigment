"""
Simple data models for the API Health Monitoring System.

The goal is to keep the types very easy to understand and to work with,
while still being explicit about what each piece of data represents.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ApiConfig:
    """
    Configuration for a single monitored API endpoint.

    These values are stored in the api_health_configs DynamoDB table.
    """

    api_id: str
    url: str
    method: str = "GET"
    expected_status_codes: List[int] = None
    timeout_ms: int = 3000
    check_interval_seconds: int = 60
    notify_emails: List[str] = None
    enabled: bool = True

    def __post_init__(self) -> None:
        # Avoid using mutable default values directly in the dataclass
        if self.expected_status_codes is None:
            self.expected_status_codes = [200]
        if self.notify_emails is None:
            self.notify_emails = []


@dataclass
class ApiHealthState:
    """
    Last known health state for an API endpoint.

    These values are stored in the api_health_states DynamoDB table.
    """

    api_id: str
    last_state: str  # "UP" or "DOWN"
    last_status_code: Optional[int]
    last_latency_ms: Optional[int]
    last_checked_at: str  # ISO 8601 timestamp
    last_changed_at: Optional[str]  # ISO 8601 timestamp
    last_error: Optional[str] = None
