## StreamSets SDK Kubernetes Deployment Example with Ingress

This project provides an example of how to use the [StreamSets Platform SDK](https://docs.streamsets.com/platform-sdk/latest/index.html) to programmatically create a [Kubernetes Deployment](https://docs.streamsets.com/portal/platform-controlhub/controlhub/UserGuide/Deployments/Kubernetes.html#concept_ec3_cqg_hvb) of [Data Collector](https://streamsets.com/products/data-collector-engine/) (SDC) using an Advanced Kubernetes configuration (as described in Step 2 [here](https://docs.streamsets.com/portal/platform-controlhub/controlhub/UserGuide/Deployments/Kubernetes.html#task_xvp_g1n_jvb)) that includes a Kubernetes Service and Ingress, with HTTPS-based access to the deployed Data Collectors.  This approach may be necessary if [Direct REST APIs](https://docs.streamsets.com/portal/platform-controlhub/controlhub/UserGuide/Engines/Communication.html#concept_dt2_hq3_34b) must be used rather than [WebSocket Tunneling](https://docs.streamsets.com/portal/platform-controlhub/controlhub/UserGuide/Engines/Communication.html#concept_hbg_fq3_34b).

### Prerequisites

- The StreamSets Organization should have WebSocket communication disabled

- An existing Kubernetes cluster with the ability to deploy an Ingress Controller. For this example I will use [ingress-nginx](https://kubernetes.github.io/ingress-nginx/deploy/) on Azure Kubernetes Service (AKS)

### Configuration Details

- This example assumes TLS will be terminated at the Load Balancer with backend communication to SDC Pods over http.  The example could easily be extended to support backend communication to SDC over https

- A custom https URL will be set in the engine's <code>sdc.base.http.url</code> property

- The engine's <code>http.enable.forwarded.requests</code> property will be set to <code>true</code>

- A Kubernetes Service and Ingress will be created for the Data Collector deployment

- Path-based routing will be configured for the Ingress

### Test Environment

- AKS using Kubernetes version v1.25.11 

- ingress-nginx version 1.6.4

- SDC version 5.6.0

### Create a Namespace for the StreamSets Deployments

Create a namespace for the StreamSets Deployment:

<code>$ kubectl create ns ns1</code>

Make that namespace the default:

<code>$ kubectl config set-context --current --namespace ns1</code>

### Deploy the Ingress Controller

I installed ingress-nginx v1.6.4 on AKS using the command:

<code>$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.6.4/deploy/static/provider/cloud/deploy.yaml</code>

### Get the External IP for the Ingress Controller's Load Balancer Service

<img src="images/external-ip.png" alt="external-ip" width="700"/>

### Map a DNS Name to the Load Balancer's IP
I added a record to my DNS to map the name <code>aks.onefoursix.com</code> to the Load Balancer's external IP, and confirm that using nslookup:

	$  nslookup aks.onefoursix.com
	Server:	8.8.8.8
	Address:	8.8.8.8#53

	Non-authoritative answer:
	Name:	aks.onefoursix.com
	Address: 20.69.83.54

### Store a TLS key and cert for the Load Balancer in a Secret
I'll use a wildcard cert and key for <code>*.onefoursix.com</code> in the files tls.crt and tls.key respectively. Store the TLS key and cert in a Kubernetes Secret:

	$ kubectl create secret tls streamsets-tls \
    	--key ~/certs/tls.key --cert ~/certs/tls.crt


### Create a Kubernetes Environment

Create a new Kubernetes Environment named <code>aks-ns1</code> and set the namespace to <code>ns1</code>. Activate the Environment but do not play the generated shell command; instead, click the <code>View Kubernetes YAML</code> button. In the dialog that opens, click the <code>copy</code> button. Paste the text into a text document on your local machine named <code>agent.yaml</code> (the name is not critical).

#### Edit the generated YAML for the Agent

On or around line 21, replace this line:

    resources: ["pods"]

with this line:

	resources: ["pods", "services"]

And add this new section:

```
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
```

That change will allow the Kubernetes Agent to create Service and Ingress resources

The updated rules section in the Role resource should look like this:

```
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "create", "patch", "delete"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "create", "patch", "delete"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "create", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "create", "patch", "delete"]
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "create", "patch", "delete"]
```


Also, if you need to set a proxy for the Kubernetes Agent, set that on or around line 102 as the value for the environment variable <code>STREAMSETS_KUBERNETES_AGENT_JAVA_OPTS</code> (for details on this step, see the docs [here](https://docs.streamsets.com/portal/platform-controlhub/controlhub/UserGuide/Environments/Kubernetes.html#task_tgv_rrg_lwb)).


#### Deploy the Agent

Apply the agent.yaml script to deploy the Agent:

	$ kubectl apply -f agent.yaml

Make sure the Agent comes online for the Environment:

<img src="images/agent.png" alt="agent" width="700"/>



