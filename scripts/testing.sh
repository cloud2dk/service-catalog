#!/bin/bash

command=$1

portfolio_name="cloud2-portfolio"
portfolio_id="port-aurywje3dopes"
product_name="cloud2-monitoring-event-management"
product_id="prod-g2qaw6zedylqk"
product_version="1.1.11"
region="eu-central-1"
operations_account_id="259252918107"
operations_event_bus_name="cloud2-events"

deploy() {
  echo "Deploying service-management"
  aws cloudformation deploy --template-file customer/service-management.yaml --stack-name ddddd --parameter-overrides OperationsAccountId=$operations_account_id OperationsEventBusName=$operations_event_bus_name --capabilities CAPABILITY_NAMED_IAM --region $region
}

terminate() {
  echo "Terminating provisioned product"
  aws servicecatalog terminate-provisioned-product --provisioned-product-name $product_name --region $region
}

import_portfolio() {
    echo "Starting automation execution"
    e=$(
    aws ssm start-automation-execution \
      --document-name "cloud2-import-portfolio" \
      --parameters "{
          \"Region\": [\"$region\"],
          \"PortfolioId\": [\"$portfolio_id\"]
      }" \
      --query "AutomationExecutionId" \
      --output text \
      --region $region
    )

  sleep 3

  echo "Checking automation execution status"
  while true; do
    
    status=$(aws ssm describe-automation-executions --region $region --filters Key=ExecutionId,Values=$e --query "AutomationExecutionMetadataList[].{Status:AutomationExecutionStatus,FailureMessage:FailureMessage}")
    if [[ $status == *"Failed"* ]]; then
        echo $status
        exit 1
    fi
    if [[ $status == *"Success"* ]]; then
        echo "Success"
        exit 0
    fi
    if [[ $status == *"InProgress"* ]]; then
        echo "Automation execution in progress"
    fi
    sleep 1
done
}

launch_product() {
    echo "Starting automation execution"
    e=$(
    aws ssm start-automation-execution \
      --document-name "cloud2-launch-product" \
      --parameters "{
          \"Region\": [\"$region\"],
          \"Version\": [\"$product_version\"],
          \"ProductId\": [\"$product_id\"],
          \"ProvisioningParameters\": [\"OperationsAccountId=$operations_account_id,OperationsEventBusName=$operations_event_bus_name\"]
      }" \
      --query "AutomationExecutionId" \
      --output text \
      --region $region
    )

  sleep 3

  echo "Checking automation execution status"
  while true; do
    
    status=$(aws ssm describe-automation-executions --region $region --filters Key=ExecutionId,Values=$e --query "AutomationExecutionMetadataList[].{Status:AutomationExecutionStatus,FailureMessage:FailureMessage}")
    if [[ $status == *"Failed"* ]]; then
        echo $status
        exit 1
    fi
    if [[ $status == *"Success"* ]]; then
        echo "Success"
        exit 0
    fi
    if [[ $status == *"InProgress"* ]]; then
        echo "Automation execution in progress"
    fi
    sleep 1
done
}

update_product() {
    echo "Starting automation execution"
    e=$(
    aws ssm start-automation-execution \
      --document-name "cloud2-update-product" \
      --parameters "{
          \"Region\": [\"$region\"],
          \"Version\": [\"$product_version\"],
          \"ProductId\": [\"$product_id\"],
          \"ProvisioningParameters\": [\"OperationsAccountId=$operations_account_id,OperationsEventBusName=$operations_event_bus_name\"]
      }" \
      --query "AutomationExecutionId" \
      --output text \
      --region $region
    )

  sleep 3

  echo "Checking automation execution status"
  while true; do
    
    status=$(aws ssm describe-automation-executions --region $region --filters Key=ExecutionId,Values=$e --query "AutomationExecutionMetadataList[].{Status:AutomationExecutionStatus,FailureMessage:FailureMessage}")
    if [[ $status == *"Failed"* ]]; then
        echo $status
        exit 1
    fi
    if [[ $status == *"Success"* ]]; then
        echo "Success"
        exit 0
    fi
    if [[ $status == *"InProgress"* ]]; then
        echo "Automation execution in progress"
    fi
    sleep 1
done
}

if [ "$command" == "import" ]; then
  import_portfolio
elif [ "$command" == "launch" ]; then
  launch_product
elif [ "$command" == "update" ]; then
  update_product
elif [ "$command" == "terminate" ]; then
  terminate
elif [ "$command" == "deploy" ]; then
  deploy
else
  echo "Invalid command"
  exit 1
fi