# Terraform CI Infrastructure

Defines infrastructure for CI-related processes.

## Github Actions Self-hosted Build Agents

On Github Actions, you can supply your own self-hosted build agents. We provide a setup for running
those agents on AWS EC2. The EC2 instance uses the Github runner service to register the build agent
in any repositories that are configured with the Github App, and this then makes it available for
use in any workflow jobs that are marked `runs-on: self-hosted`.

There are a few different components involved in the setup, so at first, it can seem confusing.
However, once explained, it's quite straight forward. Please read this section to understand the
solution.

### Github App

We have defined our own Github App, [AWS Hosted GHA Runners (Linux)](https://github.com/apps/aws-hosted-gha-runners-linux).

The app is installed on the `maidsafe` organisation and it's configured to be able to access a
single repository, `safe_network`. For repositories for which it's configured, it gets access to
their Github Actions Workflow runs. This allows it to subscribe to `Workflow job` events. Those
events occur when a job in a workflow is queued, starts, completes, and so on. When the app receives
one of those events, it posts a JSON document to a webhook. The webhook is configurable, and it can
point to absolutely anything, but in our case, it is the endpoint for an AWS Lambda function. The
Lambda will launch or stop an EC2 instance, based on the type of event. It will be described in more
detail shortly.

There are three secrets associated with the app. The first is the client secret, which is defined,
but not used as part of our solution. The second is the webhook secret, or the app secret, which is
used to validate requests sent to the webhook. The third is the private key, which is used to sign
tokens used in requests to the Github API. The API is used to register the Github build agent
service that runs on the EC2 instance.

### AWS EC2

Since we run the build agents on EC2 instances, we need a bit of infrastructure to support that:

* A VPC configured with internet access for building the AMI and fetching crates
* A security group that grants internet access
* A security group that allows SSH access to the instance for building the AMI for the build agent

### AWS Lambda

A simple Lambda function is defined in Python. It gets pushed to a Docker registry in the AWS
account and then runs in the AWS infrastructure.

The function performs the following steps:

* The workflow job event is received from a request posted to the webhook by the Github App
* The request is checked for a signature in its header
* The signature is validated using the app secret
* If the action for the workflow job is `queued`:
    - Sign a token for a Github API request using the Github App private key.
    - Use the token with an API request to get a registration token for the runner service.
    - Spin up an EC2 instance, supplying the registration token with the user data.
    - The EC2 instance will use the runner service to make the instance available to the workflow
      job
* If the action for the workflow job is `completed`:
    - Sign a token for a Github API request using the Github App private key.
    - Use the token to request the idle runners from the Github API
    - Kill the EC2 instance associated with the idle runner

## Building the Infrastructure

Install Terraform on your platform, using at least version 1.3.0.

The Terraform run will create a VPC with a NAT gateway to enable internet access. Internet access is
required for building the AMI, and the connection to the Github Actions infrastructure is also made
via port 443.

There are therefore two different security groups: one for building the AMI and the other for
running the agent during the CI process. The former group will open inbound SSH and outbound port
80/443, and the latter will only open outbound port 443.

Before the Terraform run is performed, the `secrets.tf` file must be unencrypted. It is encrypted
using `git-crypt`, which uses GPG. You need to request access from someone who has already had their
GPG key added to the repo. Once your key is added, the file can be decrypted using `git-crypt unlock`.

To create the infrastructure you should use the `gha_runner_infra` user.

Define the following environment variables:
```
AWS_ACCESS_KEY_ID=<access key ID of gha_runner_infra>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of gha_runner_infra>
```

Now run `make infrastructure`.

## Building the Runner Image

The AMI is defined using a Packer template. Install Packer on your platform, using at least version
1.8.3.

The private key for the `gha_runner_image_builder` key pair must be obtained and placed somewhere,
with `chmod 0600` permissions. If lost, a new key pair can be generated and redefined in the
`main.tf` Terraform manifest.

You should use the `gha_runner_image_builder` user.

Define the following environment variables:
```
AWS_ACCESS_KEY_ID=<access key ID of gha_runner_image_builder>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of gha_runner_image_builder>
PACKER_VAR_ssh_private_key_file_path=<path to file>
```

Now run `make build-image`.

## Create Instance Lambda Function

This process requires the creation of the Terraform infrastructure above.

The Lambda function is deployed using the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html), so install this.
You should use the `manage_runners_deploy` user for this process.

The Lambda is packaged in a Docker container, which gets pushed to the private registry on the AWS
account. You need to login to the registry with the `manage_runners_deploy` user:
```
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <AWS_ACCOUNT_NO.dkr.ecr.eu-west-2.amazonaws.com
```

Replace the account number here with our AWS account number.

Define the following environment variables:
```
AWS_ACCOUNT_NUMBER=<account number>
AWS_ACCESS_KEY_ID=<access key ID of manage_runners_deploy>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of manage_runners_deploy>
```

Now run `deploy-create-instance-function`.

## Modifying the Infrastructure

We should strive to keep the infrastructure entirely automated and avoid manual interventions.

Update the Terraform configuration to make your change, then run a `terraform plan`. Open a PR and
submit the output of the plan in the description. After review and merge, we can then run a
`terraform apply` to change the infrastructure. Soon we should be able to automate this with an
Actions workflow.
