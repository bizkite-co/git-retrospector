#!/bin/bash

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
START_TIME_MS=$(($(date +%s) * 1000 - 300000))

aws logs filter-log-events \
    --log-group-name "$LOG_GROUP_NAME" \
    --start-time $START_TIME_MS \
    --query "events[*].message" \
    --output text
