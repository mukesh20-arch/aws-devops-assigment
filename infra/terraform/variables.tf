// Input variables for the Terraform configuration.
//
// Keeping the variable set small and clear makes it easy to understand
// in an interview.

variable "aws_region" {
  description = "AWS region where the monitoring system is deployed"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (for example: dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Short name used for tagging and resource naming"
  type        = string
  default     = "api-health-monitor"
}
