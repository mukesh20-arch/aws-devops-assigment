// Outputs for the Terraform configuration.
//
// These make it easy to see the important pieces after "terraform apply".

output "ec2_instance_public_ip" {
  description = "Public IP address of the monitoring EC2 instance"
  value       = aws_instance.monitor.public_ip
}

output "dynamodb_config_table_name" {
  description = "Name of the DynamoDB table storing API configurations"
  value       = aws_dynamodb_table.api_health_configs.name
}

output "dynamodb_state_table_name" {
  description = "Name of the DynamoDB table storing API health states"
  value       = aws_dynamodb_table.api_health_states.name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic used for alerts"
  value       = aws_sns_topic.api_health_alerts.arn
}
