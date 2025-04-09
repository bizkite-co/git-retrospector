#!/bin/bash

echo "--- Fetching Initiation Lambda Logs ---"
# Get the function name from the CDK outputs (assuming stack name is RetrospectorInfraStack)
# This is a more robust way than hardcoding if the function name changes slightly
STACK_NAME="RetrospectorInfraStack"
FUNCTION_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='InitiationLambdaArn'].OutputValue" --output text)

if [ -z "$FUNCTION_ARN" ]; then
    echo "Error: Could not retrieve InitiationLambdaArn from CloudFormation outputs for stack $STACK_NAME."
    exit 1
fi

# Extract function name from ARN
FUNCTION_NAME=$(echo $FUNCTION_ARN | awk -F':' '{print $7}')

if [ -z "$FUNCTION_NAME" ]; then
    echo "Error: Could not parse function name from ARN: $FUNCTION_ARN"
    exit 1
fi

LOG_GROUP_NAME="/aws/lambda/$FUNCTION_NAME"
echo "Querying log group: $LOG_GROUP_NAME"

# Calculate start time (5 minutes ago) in milliseconds
START_TIME_MS=$(($(date +%s) * 1000 - 3000000))

aws logs filter-log-events \
    --log-group-name "$LOG_GROUP_NAME" \
    --start-time $START_TIME_MS \
    --query "events[*].message" \
    --output text

echo ""
echo "--- Fetching Latest Fargate Task Logs ---"

# Construct ECS Log Group Name
ECS_LOG_GROUP_NAME="/ecs/GitRetrospectorTask-${STACK_NAME}"
echo "Querying ECS log group: $ECS_LOG_GROUP_NAME"

# Find the latest log stream in the ECS log group
LATEST_ECS_STREAM=$(aws logs describe-log-streams \
    --log-group-name "$ECS_LOG_GROUP_NAME" \
    --order-by LastEventTime --descending --limit 1 \
    --query "logStreams[0].logStreamName" --output text)

if [ -z "$LATEST_ECS_STREAM" ] || [ "$LATEST_ECS_STREAM" == "None" ]; then
    echo "No log streams found in $ECS_LOG_GROUP_NAME."
else
    echo "Fetching logs from stream: $LATEST_ECS_STREAM"
    aws logs get-log-events \
        --log-group-name "$ECS_LOG_GROUP_NAME" \
        --log-stream-name "$LATEST_ECS_STREAM" \
        --query "events[*].message" \
        --output text
fi
