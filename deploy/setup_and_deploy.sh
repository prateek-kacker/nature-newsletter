#!/bin/bash
# Nature Weekly — AgentCore Deployment Script
# Run this once to create the IAM role and deploy the agent

set -e

ROLE_NAME="NatureWeeklyAgentCoreRole"
POLICY_NAME="NatureWeeklyAgentCorePolicy"
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "==> Step 1: Creating IAM role..."
ROLE_ARN=$(aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://deploy/iam_role.json \
  --query "Role.Arn" --output text 2>/dev/null || \
  aws iam get-role --role-name $ROLE_NAME --query "Role.Arn" --output text)

echo "    Role ARN: $ROLE_ARN"

echo "==> Step 2: Attaching policy..."
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name $POLICY_NAME \
  --policy-document file://deploy/iam_policy.json

echo "==> Step 3: Installing AgentCore toolkit..."
pip install bedrock-agentcore-starter-toolkit -q

echo "==> Step 4: Configuring agent..."
agentcore configure --entrypoint agent.py -er $ROLE_ARN

echo "==> Step 5: Launching to AgentCore Runtime..."
agentcore launch

echo ""
echo "✅ Deployment complete!"
echo "   Test with: agentcore invoke '{\"action\": \"fetch\"}'"
echo "   Logs:      agentcore status"
