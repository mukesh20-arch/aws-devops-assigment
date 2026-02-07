// SNS topic and subscriptions for notifications.
//
// We use a single topic for all alerts. Email subscriptions can be
// added here or in a separate file if needed.

resource "aws_sns_topic" "api_health_alerts" {
  name = "${var.project_name}-alerts-${var.environment}-v2"
}

// Email subscription for alerts. For this project a single email is
// enough, and it keeps the configuration easy to explain.

resource "aws_sns_topic_subscription" "alert_email" {
  topic_arn = aws_sns_topic.api_health_alerts.arn
  protocol  = "email"
  endpoint  = "bollinenimukesh20@outlook.com"
}
