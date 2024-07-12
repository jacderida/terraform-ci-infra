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

resource "aws_ecr_repository" "manage_runners" {
  name = "manage_runners"
}

resource "aws_security_group" "gha_runner" {
  name = "${var.gha_runner_security_group_name}"
  description = "Connectivity for GHA runner instances."
  vpc_id = module.vpc.vpc_id
}

# For using the GHA runner to launch a testnet, you need to have port 22 open, because Terraform
# uses SSH to check if machines have become available.
resource "aws_security_group_rule" "gha_runner_egress_ssh" {
  type = "egress"
  from_port = 22
  to_port = 22
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner.id
}

resource "aws_security_group_rule" "gha_runner_egress_http" {
  type = "egress"
  from_port = 80
  to_port = 80
  protocol = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  security_group_id = aws_security_group.gha_runner.id
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
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3RDMNQXEwJETQTRAG/ndJDESw5XwUR1NUxiegzOvj6pb0es3qUEcZGEUfFyVlSxyPZcCiizetHJMhRZN5qM/6UjUL7iDtWRLR3bq3I7iLTgZOs57QCQ/BEG70yah+xQRMDT5lt3lYxp4gKhDQgIdOtJJWEOg/KNnSP9SBZRR3Ris9rP8OiG7HR+QXDpDHwNXBVDjFGxAN3iN3osGwKO+KVai7OTT7mpzJJ0wbKvQOU+AdcqDE50POQBuyXDAm6j7mDrcLSUlNg3zDFvihbR6wcIAoUBJXoDC9LOtXuDwSw1AvS3dgC9Ij4R3eGHIobmK6qv8+ZPxe1BdxPVdjLCwb"
}

resource "aws_secretsmanager_secret" "github_app_id" {
  name = "gha_runner_github_app_id"
  # Setting the recovery window to 0 deletes the secret immediately.
  # Otherwise it will only be marked for deletion and remain for a default period of 30 days.
  # The default behaviour is really annoying for development.
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "github_app_id" {
  secret_id = aws_secretsmanager_secret.github_app_id.id
  secret_string = var.secret_github_app_id
}

resource "aws_secretsmanager_secret" "github_app_private_key_base64" {
  name = "gha_runner_github_private_key_base64"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "github_app_private_key_base64" {
  secret_id = aws_secretsmanager_secret.github_app_private_key_base64.id
  secret_string = var.secret_github_app_private_key_base64
}

resource "aws_secretsmanager_secret" "github_app_secret" {
  name = "gha_runner_github_app_secret"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "github_app_secret" {
  secret_id = aws_secretsmanager_secret.github_app_secret.id
  secret_string = var.secret_github_app_secret
}
