// AWS provider configuration for the API Health Monitoring System.
//
// This uses a small set of variables so that the same code can work in
// different regions or environments.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.5.0"
}

provider "aws" {
  region = var.aws_region

  # In a real setup you would configure credentials via environment
  # variables or a shared credentials file. For this assignment it is
  # enough to document that assumption.
}
