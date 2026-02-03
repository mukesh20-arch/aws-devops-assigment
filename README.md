# API Health Monitoring System

Self‑hosted API health monitoring service designed as a DevOps internship assignment.  
The goal is to show clear thinking about reliability, AWS, and Terraform rather than to build a full product.

## 1. Problem the system solves

Many teams have a few critical HTTP APIs and just want to know:

- Is the endpoint returning the status code we expect?
- How fast is it responding?
- Did it just go from **UP → DOWN** or **DOWN → UP**?

This project provides a small service that:

- Periodically checks user‑defined API endpoints.
- Stores their configuration and last known state.
- Sends an email alert when the state changes (UP ↔ DOWN).
- Runs entirely on AWS using basic building blocks (EC2, DynamoDB, SNS, IAM).

No external or managed monitoring tools are used.

## 2. High‑level architecture

**Main components**

- **API Config Store (DynamoDB)**
  - Table `api_health_configs` stores one item per monitored API:
    - `api_id`, `url`, `method`, `expected_status_codes`, `timeout_ms`,
      `check_interval_seconds`, `notify_emails`, `enabled`.
- **State Store (DynamoDB)**
  - Table `api_health_states` stores the last known state per API:
    - `api_id`, `last_state` (`UP` / `DOWN`), `last_status_code`,
      `last_latency_ms`, `last_checked_at`, `last_changed_at`, `last_error`.
- **Scheduler (cron on EC2)**
  - A cron job on the EC2 instance runs the Python entrypoint on a fixed schedule
    (for example, every 2 minutes).
- **Health Checker (Python)**
  - Makes HTTP requests to each configured API.
  - Applies simple rules based on expected status codes and timeout.
- **State Tracker (Python + DynamoDB)**
  - Reads the previous state from `api_health_states`.
  - Compares it with the current result.
- **Notifier (SNS)**
  - When state changes (UP ↔ DOWN), publishes a message to an SNS topic.
  - Email subscribers receive the alert.

In words, the flow is:

> cron → Python app on EC2 → read configs from DynamoDB → call APIs → compare with last state →  
> if changed, send SNS alert → store new state in DynamoDB.

## 3. AWS infrastructure (Terraform)

All infrastructure is managed with Terraform under `infra/terraform`.

**Services used**

- **EC2**
  - Single Ubuntu EC2 instance running the Python monitoring app.
  - `user_data` installs Python and tools; in a real setup this is where the app code
    would be deployed and the cron job configured.
- **DynamoDB**
  - `api_health_configs` – configuration for each monitored API.
  - `api_health_states` – last known health state for each API.
  - Both use on‑demand billing (`PAY_PER_REQUEST`) to avoid capacity planning.
- **SNS**
  - One topic for alerts: `${var.project_name}-alerts-${var.environment}`.
  - Email subscriptions can be added via Terraform.
- **IAM**
  - An IAM role for the EC2 instance with least‑privilege access:
    - Read/write on both DynamoDB tables.
    - `sns:Publish` on the alert topic.
  - Instance profile attaches this role to the EC2 instance.
- **Networking**
  - A basic security group:
    - Allows SSH (22) for administration.
    - Allows all outbound so the instance can call external APIs.
  - In a production setup, SSH would be restricted to a known IP range.

**Key Terraform files**

- `provider.tf` – AWS provider and Terraform version.
- `variables.tf` – region, environment, project name.
- `dynamodb.tf` – both DynamoDB tables.
- `sns.tf` – SNS topic (and example subscription).
- `iam.tf` – IAM role, policy and instance profile for the EC2 instance.
- `ec2.tf` – AMI lookup, security group, and EC2 instance definition.
- `outputs.tf` – EC2 public IP, DynamoDB table names, SNS topic ARN.

## 4. Application design (Python)

Python code lives under `app/src`.

- `config.py`
  - Reads configuration from environment variables (region, table names, SNS topic ARN).
  - Uses a small `AppConfig` dataclass so it is clear what the app depends on.
- `models.py`
  - `ApiConfig` dataclass: shape of one monitored API.
  - `ApiHealthState` dataclass: shape of one stored health state.
- `dynamodb_client.py`
  - Wrapper around `boto3` to:
    - Scan the `api_health_configs` table and return a list of `ApiConfig` objects.
    - Get and update `ApiHealthState` objects in the `api_health_states` table.
- `sns_client.py`
  - Small helper to publish text alerts to the SNS topic.
- `health_checker.py`
  - Accepts an `ApiConfig`, makes an HTTP request using `requests`,
    and returns:
    - `state` (`UP` / `DOWN`)
    - `status_code`
    - `latency_ms`
    - `error` text if something went wrong.
- `monitor_runner.py`
  - Main orchestration for a single monitoring pass:
    - Loads all API configs.
    - Runs health checks.
    - Looks up the previous state from DynamoDB.
    - Detects UP ↔ DOWN changes.
    - Sends alerts via SNS on change.
    - Stores the new state back into DynamoDB.
- `cron_entrypoint.py`
  - Tiny entrypoint that just calls `run_monitor_once()`.
  - This is what cron will execute on a schedule.

## 5. Health check and alerting flow

Conceptually, one monitoring run does this for each API:

1. Read API config from `api_health_configs`.
2. Make an HTTP request to the API.
3. Check if the response:
   - Completed within the configured timeout.
   - Returned one of the expected status codes.
4. Decide current state:
   - If both conditions pass → `UP`.
   - Otherwise (timeout, error, or wrong status) → `DOWN`.
5. Load the last stored state from `api_health_states`.
6. If last state is different from current state (or does not exist yet):
   - Build a simple text message with details.
   - Publish it to the SNS topic (email notification).
7. Store the new state (including timestamps and any error text) back to DynamoDB.

This behaviour matches the requirement to only notify on **meaningful** state changes
instead of spamming alerts on every check.

## 6. Scaling and reliability considerations

Even though this implementation is small, it is designed so it can grow:

- **More APIs**
  - DynamoDB scales automatically with on‑demand billing.
  - If the number of APIs becomes large, the `scan` in `dynamodb_client.py`
    can be changed to use pagination or filters.
- **More workers**
  - Instead of a single EC2 instance, multiple instances (or ECS tasks)
    can run the same code, each responsible for a subset of APIs.
- **Splitting work**
  - In a larger system, checks could be pushed to a queue (for example SQS),
    and multiple workers could pull from that queue to spread the load.
- **Failure handling**
  - Timeouts and request errors are treated as `DOWN` so failures are visible.
  - State is stored in DynamoDB, so a restarted instance can continue where
    it left off.
  - If SNS or DynamoDB are temporarily unavailable, the failure is limited
    to that run; the next run can continue normally.

These ideas are simple to describe in an interview and show that the design
can be extended without completely rewriting it.

## 7. Deployment steps (high level)

1. **Prepare AWS credentials**
   - Configure AWS credentials locally (for example with `aws configure`).
   - Make sure your user/role can create EC2, DynamoDB, SNS and IAM resources.
2. **Terraform apply**
   - Change into `infra/terraform`.
   - Run:
     - `terraform init`
     - `terraform plan`
     - `terraform apply`
   - Note the outputs:
     - EC2 public IP
     - DynamoDB table names
     - SNS topic ARN
3. **Deploy application code**
   - SSH into the EC2 instance using the public IP.
   - Install the app code (for example by cloning the repository).
   - Install dependencies:
     - `pip install -r app/requirements.txt`
   - Set environment variables:
     - `AWS_REGION`, `APP_ENVIRONMENT`, `DDB_CONFIG_TABLE`,
       `DDB_STATE_TABLE`, `SNS_TOPIC_ARN`.
4. **Configure cron**
   - Add a cron entry that runs the monitor periodically, for example (every 2 minutes):
     - `*/2 * * * * cd /path/to/project && python3 -m app.src.cron_entrypoint >> /var/log/api-monitor.log 2>&1`

After this, the system will run checks on the configured schedule and send
email alerts on meaningful state changes.

## 8. Diagrams (how to visualise)

For documentation and interviews, the system can be drawn as:

- **Architecture diagram**
  - User → defines APIs (stored in DynamoDB `api_health_configs`).
  - EC2 instance → reads configs, calls APIs, updates `api_health_states`.
  - EC2 instance → publishes alerts to SNS → email subscribers.
- **Flow diagram**
  - `cron` → `health checker` → `state tracker` → `SNS` → email.

Even a simple hand‑drawn version that shows these components and arrows is
enough to explain the design clearly.
