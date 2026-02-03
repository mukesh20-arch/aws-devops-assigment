// EC2 instance and related networking resources.
//
// This keeps the setup simple: one instance, one security group.

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] // Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "monitor_sg" {
  name        = "${var.project_name}-sg-${var.environment}"
  description = "Security group for API health monitoring instance"

  // Allow SSH from anywhere for simplicity in the assignment.
  // In a real setup, this should be restricted to your IP.
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  // Allow all outbound so the instance can call external APIs.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "monitor" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = "monitor-key-2"

  iam_instance_profile = aws_iam_instance_profile.monitor_instance_profile.name
  vpc_security_group_ids = [
    aws_security_group.monitor_sg.id,
  ]

  tags = {
    Name        = "${var.project_name}-ec2-${var.environment}"
    Environment = var.environment
  }

  user_data = <<-EOF
              #!/bin/bash
              # Simple bootstrap script for the monitoring app.
              apt-get update -y
              apt-get install -y python3 python3-pip git

              # Placeholder: in a real setup you would clone the repo or
              # copy the application code here and set up a cron job.
              EOF
}
