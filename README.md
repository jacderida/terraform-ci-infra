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

To create the infrastructure you will need an IAM user with the following permissions:
```
ec2:AllocateAddress
ec2:AssociateRouteTable
ec2:AttachInternetGateway
ec2:AuthorizeSecurityGroupIngress
ec2:AuthorizeSecurityGroupEgress
ec2:CreateVpc
ec2:CreateInternetGateway
ec2:CreateNatGateway
ec2:CreateRoute
ec2:CreateRouteTable
ec2:CreateSecurityGroup
ec2:CreateSubnet
ec2:CreateTags
ec2:DeleteKeypair
ec2:DeleteNatGateway
ec2:DeleteRoute*
ec2:DeleteSecurityGroup
ec2:DeleteSubnet*
ec2:DeleteVpc
ec2:Describe*
ec2:DeleteInternetGateway
ec2:DetachInternetGateway
ec2:DisassociateAddress
ec2:DisassociateRouteTable
ec2:ImportKeyPair
ec2:ModifySubnetAttribute
ec2:ModifyVpcAttribute
ec2:ReleaseAddress
ec2:RevokeSecurityGroupIngress
ec2:RevokeSecurityGroupEgres
```

In addition, the user will need to be able to read the Terraform state, which is stored in an S3
bucket. It's most likely this user will be defined in our other repository, `terraform-org-infra`.

Define the following environment variables:
```
AWS_ACCESS_KEY_ID=<access key ID of user>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of user>
```

Now run `make infrastructure`.

## Building the Runner Image

The AMI is defined using a Packer template. Install Packer on your platform, using at least version
1.8.3.

To create the image you will need an IAM user with the following permissions:
```
ec2:CreateImage
ec2:CreateTags
ec2:Describe*
ec2:RunInstances
ec2:StopInstances
ec2:TerminateInstances
```

The user also needs to be able to read the Terraform state, because values are supplied to Packer
from the Terraform output. As with the Terraform run, it's most likely this user will have already
been defined in our other repository.

The private key for the `gha_runner_image_builder` must be obtained and placed somewhere, with
`chmod 0600` permissions. If lost, a new key pair can be generated and redefined in the `main.tf`
Terraform manifest.

Define the following environment variables:
```
AWS_ACCESS_KEY_ID=<access key ID of user>
AWS_DEFAULT_REGION=eu-west-2
AWS_SECRET_ACCESS_KEY=<secret access key of user>
PACKER_VAR_ssh_private_key_file_path=<path to file>
```

Now run `make build-image`.

## Modifying the Infrastructure

We should strive to keep the infrastructure entirely automated and avoid manual interventions.

Update the Terraform configuration to make your change, then run a `terraform plan`. Open a PR and
submit the output of the plan in the description. After review and merge, we can then run a
`terraform apply` to change the infrastructure. Soon we should be able to automate this with an
Actions workflow.
