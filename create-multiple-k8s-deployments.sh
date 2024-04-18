#!/usr/bin/env bash

# Check the number of arguments
if [ "$#" -ne 2 ]; then
    echo "Wrong number of arguments"
    echo "Usage: ./create-k8s-deployment.sh  <environment-name> <deployment-suffix-1>[,<deployment-suffix-2>[,<deployment-suffix-2>[...]],"
    echo "Example ./create-k8s-deployment.sh env-1 sdc1,sdc2,sdc3"
    exit 9
fi

# Set Control Hub credentials
source private/sdk-env.sh

export ENV_NAME=${1}

DEPLOYMENT_SUFFIX_LIST=${2}

echo "---------"
echo "Creating StreamSets Deployments"
echo "Environment Name" $ENV_NAME
echo "Deployment Suffix List:" $DEPLOYMENT_SUFFIX_LIST
echo "---------"
echo ""

index=0
for suffix in ${DEPLOYMENT_SUFFIX_LIST//,/ }
do
  echo "---------"
  echo "Creating StreamSets Deployment"
  echo "Environment Name" $ENV_NAME
  echo "SDC Suffix:" "$suffix"
  echo "---------"
  export DEPLOYMENT_SUFFIX=${suffix}
  export DEPLOYMENT_INDEX=${index}

  # Launch the SDK script
  python python/create-k8s-deployment.py

  # Bump the deployment index
  index=$((index+1))
done






