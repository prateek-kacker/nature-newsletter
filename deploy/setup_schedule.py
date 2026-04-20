"""
setup_schedule.py — Creates the AWS infrastructure for weekly scheduling.

Sets up:
  1. S3 bucket for caching the weekly issue
  2. EventBridge rule to trigger the AgentCore agent every Thursday at 9AM UTC
  3. IAM permissions for EventBridge to invoke AgentCore

Run once after deploying the agent:
  python deploy/setup_schedule.py --agent-arn <your-agent-arn>
"""
import boto3
import json
import argparse
import sys

REGION = "us-east-1"
BUCKET_NAME = "nature-weekly-cache"
RULE_NAME = "NatureWeeklyThursdayRefresh"
SCHEDULE = "cron(0 9 ? * 5 *)"  # Every Thursday at 9AM UTC


def create_s3_bucket(s3):
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
        print(f"✓ S3 bucket created: {BUCKET_NAME}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ S3 bucket already exists: {BUCKET_NAME}")
    except Exception as e:
        print(f"✗ S3 bucket error: {e}")
        sys.exit(1)


def create_eventbridge_rule(events, agent_arn):
    # Create the schedule rule
    events.put_rule(
        Name=RULE_NAME,
        ScheduleExpression=SCHEDULE,
        State="ENABLED",
        Description="Triggers Nature Weekly agent every Thursday at 9AM UTC",
    )
    print(f"✓ EventBridge rule created: {RULE_NAME} ({SCHEDULE})")

    # Add the AgentCore agent as the target
    events.put_targets(
        Rule=RULE_NAME,
        Targets=[{
            "Id": "NatureWeeklyAgentTarget",
            "Arn": agent_arn,
            "Input": json.dumps({"action": "refresh"}),
        }]
    )
    print(f"✓ Target set: {agent_arn}")


def update_iam_role_for_s3(iam, role_name):
    """Add S3 write permission to the AgentCore execution role."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject", "s3:CreateBucket"],
            "Resource": [
                f"arn:aws:s3:::{BUCKET_NAME}",
                f"arn:aws:s3:::{BUCKET_NAME}/*"
            ]
        }]
    }
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="NatureWeeklyS3CachePolicy",
        PolicyDocument=json.dumps(policy)
    )
    print(f"✓ S3 policy attached to role: {role_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-arn", required=True, help="AgentCore agent ARN")
    parser.add_argument("--role-name", default="NatureWeeklyAgentCoreRole")
    args = parser.parse_args()

    s3 = boto3.client("s3", region_name=REGION)
    events = boto3.client("events", region_name=REGION)
    iam = boto3.client("iam")

    print("\n==> Setting up weekly schedule infrastructure...\n")
    create_s3_bucket(s3)
    update_iam_role_for_s3(iam, args.role_name)
    create_eventbridge_rule(events, args.agent_arn)

    print(f"""
✅ Done! Weekly schedule configured.

   Every Thursday at 9AM UTC:
     EventBridge → AgentCore agent → fetches Nature RSS
                 → Claude AI rewrites summaries
                 → saves to s3://{BUCKET_NAME}/latest.json

   Web app reads from S3 cache on every user visit.

   To trigger manually:
     agentcore invoke '{{"action": "refresh"}}'
""")


if __name__ == "__main__":
    main()
