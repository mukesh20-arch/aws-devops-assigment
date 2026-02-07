"""
SNS client helpers for the API Health Monitoring System.

The goal here is to keep things very simple: one helper that knows how
to publish a plain text message to the SNS topic.
"""

import boto3

from .config import get_config


def _get_sns_client():
    cfg = get_config()
    return boto3.client("sns", region_name=cfg.aws_region)


def send_alert(subject: str, message: str) -> None:
    """
    Publish a basic alert message to the SNS topic.

    The subscriber (email) will receive the subject and message as a
    normal email. For this project we do not need any complex
    formatting.
    """
    cfg = get_config()
    if not cfg.sns_topic_arn:
        # In a real system we might log this somewhere. For now we just
        # avoid throwing an exception so the monitor can keep running.
        return

    client = _get_sns_client()
    client.publish(TopicArn=cfg.sns_topic_arn, Subject=subject, Message=message)
