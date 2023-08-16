#!/usr/bin/env bash

# Check the number of arguments
if [ "$#" -ne 2 ]; then
    echo "Wrong number of arguments"
    echo "Usage: ./create-k8s-deployment.sh  <environment-name> <deployment-suffix>"
    echo "Example ./create-k8s-deployment.sh env-1 sdc1"
    exit 9
fi

# Set Control Hub credentials
source private/sdk-env.sh

export ENV_NAME=${1}
export DEPLOYMENT_SUFFIX=${2}

echo "---------"
echo "Creating StreamSets Deployment"
echo "Environment Name" $ENV_NAME
echo "DEPLOYMENT_SUFFIX:" $DEPLOYMENT_SUFFIX
echo "---------"
echo ""

# Launch the SDK script
python python/create-k8s-deployment.py

