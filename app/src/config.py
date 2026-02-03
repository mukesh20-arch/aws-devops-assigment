"""
Simple configuration helper for the API Health Monitoring System.

All values come from environment variables so that we do not hard-code
AWS resource names or regions in the code. This is easy to explain in
an interview and is a common basic pattern.
"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Configuration values used by the health monitoring app."""

    aws_region: str
    environment: str
    dynamodb_config_table: str
    dynamodb_state_table: str
    sns_topic_arn: str


def get_config() -> AppConfig:
    """
    Load configuration from environment variables.

    Keeping this logic in one place makes it easy to see what the app
    depends on and to document it in the README.
    """
    return AppConfig(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        environment=os.getenv("APP_ENVIRONMENT", "dev"),
        dynamodb_config_table=os.getenv("DDB_CONFIG_TABLE", "api_health_configs"),
        dynamodb_state_table=os.getenv("DDB_STATE_TABLE", "api_health_states"),
        sns_topic_arn=os.getenv("SNS_TOPIC_ARN", ""),
    )
