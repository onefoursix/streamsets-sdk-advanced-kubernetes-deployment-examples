#!/usr/bin/env python

'''
This script creates and optionally starts a Kubernetes Deployment on StreamSets Platform

Prerequisites:
 - Python 3.6+

 - StreamSets DataOps Platform SDK for Python v5.1+
   See: https://docs.streamsets.com/platform-sdk/latest/learn/installation.html

 - DataOps Platform API Credentials for a user with Organization Administrator role

 - An active StreamSets Kubernetes Environment with an online Kubernetes Agent 

'''

import datetime, os, sys
from configparser import ConfigParser
from streamsets.sdk import ControlHub


# print_message method which writes a timestamp message to the console
def print_message(message):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' +   message)

# Method to read a deployment property
def get_deployment_property(key):
    value = deployment_properties[key]
    if value is None:
        print('Error: no value for deployment property key \'' + key + '\'' )
        print('Script will exit')
        sys.exit(-1)
    return value

# Get Control Hub API credentials from the environment
cred_id = os.getenv('CRED_ID')
cred_token = os.getenv('CRED_TOKEN')

# Get the Environment Name and Deployment Suffix from the environment.
# This makes it easier to support the creation of 
# multple identical deployments from a top-level driver script 
# that may call this script multiple times.  In such cases
# all the values read from deployment.properties file remain the same. 
# The only values that might change are the deployment suffix, 
# which might have values like 'sdc1', 'sdc2', 'sdc3', etc...
# or the Environment name
env_name = os.getenv('ENV_NAME')
deployment_suffix = os.getenv('DEPLOYMENT_SUFFIX')

# Read the deployment.properties file
config = ConfigParser()
config.read('deployment.properties')
deployment_properties = config['deployment']

# Get the values in the deployment.properties file
sch_url = get_deployment_property('SCH_URL')
org_id = get_deployment_property('ORG_ID')
environment_name = get_deployment_property('ENVIRONMENT_NAME')
load_balancer_hostname = get_deployment_property('LOAD_BALANCER_HOSTNAME')
sdc_deployment_manifest= get_deployment_property('SDC_DEPLOYMENT_MANIFEST')
sdc_version = get_deployment_property('SDC_VERSION')
deployment_tags = get_deployment_property('DEPLOYMENT_TAGS')
user_stage_libs = get_deployment_property('USER_STAGE_LIBS')
engine_labels = get_deployment_property('ENGINE_LABELS')
sdc_max_cpu_load = get_deployment_property('SDC_MAX_CPU_LOAD')
sdc_max_memory_used = get_deployment_property('SDC_MAX_MEMORY_USED')
sdc_max_pipelines_running = get_deployment_property('SDC_MAX_PIPELINES_RUNNING')
sdc_java_min_heap_mb = get_deployment_property('SDC_JAVA_MIN_HEAP_MB')
sdc_java_max_heap_mb = get_deployment_property('SDC_JAVA_MAX_HEAP_MB')
sdc_java_opts = get_deployment_property('SDC_JAVA_OPTS')
requests_memory = get_deployment_property('REQUESTS_MEMORY')
limits_memory = get_deployment_property('LIMITS_MEMORY')
requests_cpu = get_deployment_property('REQUESTS_CPU')
limits_cpu = get_deployment_property('LIMITS_CPU')


# Connect to Control Hub
print_message('Connecting to Control Hub')
sch = ControlHub(credential_id=cred_id, token=cred_token)

# Get the environment
print_message('Getting the environment')
environment = sch.environments.get(environment_name = environment_name)
print_message('Found environment ' + environment_name)

# Get the environment's namespace
namespace = environment.kubernetes_namespace
print_message('Using namespace ' + namespace)

# Create a deployment builder
print_message('Creating a deployment builder')
deployment_builder = sch.get_deployment_builder(deployment_type='KUBERNETES')

# Create the name for the deployment
deployment_name = environment_name + '-' + deployment_suffix

# Create the deployment
print_message('Creating deployment ' + deployment_name)
deployment_tags_array = deployment_tags.split(',')
deployment = deployment_builder.build(deployment_name=deployment_name,
                                      environment=environment,
                                      engine_type='DC',
                                      engine_version=sdc_version,
                                      deployment_tags=deployment_tags_array)

# Add the deployment to Control Hub
sch.add_deployment(deployment)

# These stage libs always need to be included
deployment.engine_configuration.stage_libs = ['dataformats', 'dev', 'basic']

# Add user stage libs to the Deployment
print_message('Adding Stage Libs: ' + user_stage_libs) 
stage_libs_to_add = user_stage_libs.split(',')
deployment.engine_configuration.stage_libs.extend(stage_libs_to_add)

# Engine config
engine_config = deployment.engine_configuration
engine_config.engine_labels.extend(engine_labels.split(','))
engine_config.max_cpu_load = sdc_max_cpu_load
engine_config.max_memory_used = sdc_max_memory_used
engine_config.max_pipelines_running = sdc_max_pipelines_running

# Engine Java config
java_config = engine_config.java_configuration
java_config.java_memory_strategy = 'ABSOLUTE'
java_config.minimum_java_heap_size_in_mb=sdc_java_min_heap_mb
java_config.maximum_java_heap_size_in_mb=sdc_java_max_heap_mb
java_config.java_options = sdc_java_opts

# Advanced Engine config
advanced_engine_config = engine_config.advanced_configuration

# sdc.properties
print_message('Loading sdc.properties') 
with open('etc/sdc.properties') as f:
    sdc_properties = f.read()
sdc_url = 'https://' + load_balancer_hostname + '/' + deployment_suffix + '/'
sdc_properties = sdc_properties.replace('${SDC_BASE_HTTP_URL}', sdc_url)
advanced_engine_config.data_collector_configuration = sdc_properties

# credential-stores.properties
print_message('Loading credential-stores.properties') 
with open('etc/credential-stores.properties') as f:
    credential_stores = f.read()
advanced_engine_config.credential_stores = credential_stores

# security_policy
print_message('Loading security.policy') 
with open('etc/security.policy') as f:
    security_policy = f.read()
advanced_engine_config.security_policy = security_policy

# log4j2
print_message('Loading sdc-log4j2.properties') 
with open('etc/sdc-log4j2.properties') as f:
    log4j2 = f.read()
advanced_engine_config.log4j2 = log4j2

# proxy.properties
print_message('Loading proxy.properties') 
with open('etc/proxy.properties') as f:
    proxy_properties = f.read()
advanced_engine_config.proxy_properties = proxy_properties

# Update the deployment
sch.update_deployment(deployment)

# Set advanced mode to True to support custom YAML
deployment._data["advancedMode"]=True

# Load the SDC Deployment manifest from the file
print_message('Using yaml template: ' + sdc_deployment_manifest) 
with open(sdc_deployment_manifest) as f:
    yaml = f.read()

# Get the first part of the deployment ID
short_deployment_id = deployment.deployment_id[0:deployment.deployment_id.index(':')]

# Replace the tokens in the YAML template
yaml = yaml.replace('${DEP_ID}', short_deployment_id)
yaml = yaml.replace('${NAMESPACE}', namespace)
yaml = yaml.replace('${SDC_VERSION}', sdc_version)
yaml = yaml.replace('${ORG_ID}', org_id)
yaml = yaml.replace('${SCH_URL}', sch_url)
yaml = yaml.replace('${REQUESTS_MEMORY}', requests_memory)
yaml = yaml.replace('${LIMITS_MEMORY}', limits_memory)
yaml = yaml.replace('${REQUESTS_CPU}', requests_cpu)
yaml = yaml.replace('${LIMITS_CPU}', limits_cpu)
yaml = yaml.replace('${DEPLOYMENT_SUFFIX}', deployment_suffix)
yaml = yaml.replace('${LOAD_BALANCER_HOSTNAME}', load_balancer_hostname)

# Assign the yaml to the deployment
deployment.yaml = yaml

# Update the deployment
sch.update_deployment(deployment)

# (Optional) Start the deployment
# sch.start_deployment(deployment)
print_message('Done')