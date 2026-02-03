// IAM roles and instance profiles.
//
// The EC2 instance needs permission to read/write DynamoDB tables and
// publish to the SNS topic.

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "monitor_instance_role" {
  name               = "${var.project_name}-ec2-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

data "aws_iam_policy_document" "monitor_instance_policy" {
  statement {
    sid    = "DynamoDBAccess"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan",
      "dynamodb:Query",
    ]

    resources = [
      aws_dynamodb_table.api_health_configs.arn,
      aws_dynamodb_table.api_health_states.arn,
    ]
  }

  statement {
    sid    = "SNSPublish"
    effect = "Allow"

    actions = [
      "sns:Publish",
    ]

    resources = [
      aws_sns_topic.api_health_alerts.arn,
    ]
  }
}

resource "aws_iam_policy" "monitor_instance_managed_policy" {
  name   = "${var.project_name}-policy-${var.environment}"
  policy = data.aws_iam_policy_document.monitor_instance_policy.json
}

resource "aws_iam_instance_profile" "monitor_instance_profile" {
  name = "${var.project_name}-instance-profile-${var.environment}"
  role = aws_iam_role.monitor_instance_role.name
}
