// DynamoDB tables used by the API Health Monitoring System.
//
// We keep the design simple and use two tables:
// - api_health_configs: one item per monitored API, stores configuration
// - api_health_states: one item per monitored API, stores last known state

resource "aws_dynamodb_table" "api_health_configs" {
  name         = "api_health_configs"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "api_id"

  attribute {
    name = "api_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "api_health_states" {
  name         = "api_health_states"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "api_id"

  attribute {
    name = "api_id"
    type = "S"
  }
}
