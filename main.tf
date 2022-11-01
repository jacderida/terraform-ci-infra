terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  backend "s3" {
    bucket = "maidsafe-org-infra-tfstate"
    key    = "terraform-ci-infra.tfstate"
    region = "eu-west-2"
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.18.0"
  name = var.subnet_name
  cidr = "10.0.0.0/16"
  azs = var.availability_zones
  public_subnets = ["10.0.0.0/24"]
  private_subnets = ["10.0.1.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = true
  enable_dns_hostnames = false
  enable_dns_support = true
}

resource "aws_sqs_queue" "build" {
  name                        = "gha-runner-builds"
  delay_seconds               = 90
  message_retention_seconds   = 86400
  receive_wait_time_seconds   = 10
}

resource "aws_sqs_queue" "workflow" {
  name                        = "gha-runner-webhook"
  delay_seconds               = 90
  message_retention_seconds   = 86400
  receive_wait_time_seconds   = 10
}

module "webhook" {
  source  = "./modules/webhook"
  sqs_build_queue = {
    id = aws_sqs_queue.build.id
    arn = aws_sqs_queue.build.arn
  }
  sqs_workflow_job_queue = {
    id = aws_sqs_queue.workflow.id
    arn = aws_sqs_queue.workflow.arn
  }
  webhook_file_path = "./lambda/webhook/webhook.zip"
  lambda_iam_role = var.lambda_iam_role
}

resource "aws_security_group" "gha_runner" {
  name = "${var.gha_runner_security_group_name}"
  description = "Connectivity for GHA runner instances."
  vpc_id = module.vpc.vpc_id
}

resource "aws_security_group_rule" "gha_runner_egress_https" {
  type = "egress"
  from_port = 443
  to_port = 443
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner.id
}

resource "aws_security_group" "gha_runner_image_builder" {
  name = var.gha_runner_image_security_group_name
  description = "Connectivity for Packer for building the GHA runner AMI."
  vpc_id = module.vpc.vpc_id
}

# The image building process needs SSH inbound and outbound internet connectivity.
#
# These need to be explicitly enabled when using VPC/NAT. After the image has been built, only HTTPs
# will be required during the CI process.
resource "aws_security_group_rule" "gha_runner_image_builder_ingress_ssh" {
  type = "ingress"
  from_port = 22
  to_port = 22
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner_image_builder.id
}

resource "aws_security_group_rule" "gha_runner_image_builder_egress_http" {
  type = "egress"
  from_port = 80
  to_port = 80
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner_image_builder.id
}

resource "aws_security_group_rule" "gha_runner_image_builder_egress_https" {
  type = "egress"
  from_port = 443
  to_port = 443
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner_image_builder.id
}

resource "aws_key_pair" "gha_runner_image_builder" {
  key_name = var.gha_runner_image_builder_key_name
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDAY9iAxRT1zBwy8Zf9p9pR0rHwEaOL/6aGsQ2X70emFDVED+ms6w0Rgm8uEaZ1g2r/MBuiz3KlNEXcBrlcPkHIX+80/3ypvJtuH2h6t56cs8lVO8PJFeaBYEJstXEOf/QKDFIUPTstZH95lnyHS+11HQ5gxlHGMHW3tepXnZ3rN5BJzGGzhEWd/U50saBRgE0g4GHGebZprGPteRNGASwJXNRIbzwNdPUbIwxQBhwVrI15Sz/o4bvjGd1AfUgy4OMbrOQPVZHFD75K1w4rQeEQ6fGGHiV1rjuKBVgyeRmqPS3rVHss3Wq11GtHTGGxsMC4OLH4zosmoMrdO4gwvl/O8T7u6LadO/7ACMqGd7ctfLAlW1jqRPz1BSxklQgwAPduvBNvV81RV6B59ChltJa83X42BG6KkJAMIyfnNchuR2BALGutILWh8ualOl501qTaF+sPVM0HqjK9ow0lRU3UX9n4RvqEmS+Onch7SiTn5tBpDmikxhboADDhyczJ0/0="
}
