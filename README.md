# Terraform CI Infrastructure

Defines infrastructure for CI-related processes.

We have a requirement for build agents with improved speed and memory capacity than those offered by
the Github Actions infrastructure. This repository automates the creation of a VPC where EC2
instances can be launched and used as a runner for a job in Github Actions. The image for the runner
is also automated. Both configurations can be extended as need be, as and when new requirements
arise.

There are instructions for building the infrastructure, but we may also automate these processes
using Github Actions workflows.

## Building the Infrastructure

Install Terraform on your platform, using at least version 1.3.0.

The Terraform run will create a VPC with a NAT gateway to enable internet access. Internet access is
required for building the AMI, and the connection to the Github Actions infrastructure is also made
via port 443.

There are therefore two different security groups: one for building the AMI and the other for
running the agent during the CI process. The former group will open inbound SSH and outbound port
80/443, and the latter will only open outbound port 443.

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

## Deploying the Create Instance Lambda Function

This process requires the creation of the Terraform infrastructure above.

The Github app for the self-hosted runner is installed at the organisation level. The app allows you
to provide a webhook where it will post a `workflow_job` event. This webhook hits an AWS Lambda
function, which then launches an EC2 instance.

The Lambda function is deployed using the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html), so install this.
You should use the `gha_runner_deploy` user for this process.

The Lambda is packaged in a Docker container, which gets pushed to the private registry on the AWS
account. You need to login to the registry with the `gha_runner_deploy` user:
```
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <AWS_ACCOUNT_NO.dkr.ecr.eu-west-2.amazonaws.com
```

Replace the account number here with our AWS account number.

Define the following environment variables:
```
AWS_ACCOUNT_NUMBER=<account number>
AWS_ACCESS_KEY_ID=<access key ID of gha_runner_image_builder>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of gha_runner_image_builder>
```

Now run `deploy-create-instance-function`.

## Modifying the Infrastructure

We should strive to keep the infrastructure entirely automated and avoid manual interventions.

Update the Terraform configuration to make your change, then run a `terraform plan`. Open a PR and
submit the output of the plan in the description. After review and merge, we can then run a
`terraform apply` to change the infrastructure. Soon we should be able to automate this with an
Actions workflow.
