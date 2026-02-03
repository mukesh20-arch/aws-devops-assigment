"""
Cron entrypoint script for the API Health Monitoring System.

This module is what the cron job on the EC2 instance will call. It keeps
the logic very small: just run one monitoring pass.
"""

from .monitor_runner import run_monitor_once


if __name__ == "__main__":
    run_monitor_once()
