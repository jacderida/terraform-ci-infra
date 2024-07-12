packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

locals {
  ami_name = "gha-runner-ubuntu-22.04-LTS-${formatdate("YYYY-MM-DD-hh-mm-ss", timestamp())}"
}

variable "instance_type" {
  type = string
  default = "t2.medium"
  description = "This instance type is 4GB of RAM and 2xCPU"
}

variable "region" {
  type = string
  default = "eu-west-2"
  description = "The region the instance will be launched into"
}

variable "base_ami_image_id" {
  type = string
  default = "ami-0f540e9f488cfa27d"
  description = "The image ID for Amazon's base Ubuntu 22.04LTS image"
}

variable "subnet_id" {
  type = string
  description = "The ID of the public subnet for the VPC the instance will be launched into"
}

variable "security_group_id" {
  type = string
  description = "The ID of the security group the instance will be launched into"
}

variable "ssh_username" {
  type = string
  default = "ubuntu"
  description = "The default user for Amazon's Ubuntu image"
}

variable "ssh_private_key_file_path" {
  type = string
  default = "~/.ssh/gha_runner_image_builder"
  description = "Path to the private key for the gha_runner_image_builder keypair"
}

variable "ssh_keypair_name" {
  type = string
  default = "gha_runner_image_builder"
  description = "The name of the EC2 keypair to launch the instance with"
}

source "amazon-ebs" "ubuntu" {
  ami_name             = local.ami_name
  instance_type        = var.instance_type
  region               = var.region
  source_ami           = var.base_ami_image_id
  subnet_id            = var.subnet_id
  security_group_id    = var.security_group_id
  ssh_username         = var.ssh_username
  ssh_private_key_file = var.ssh_private_key_file_path
  ssh_keypair_name     = var.ssh_keypair_name

  ami_block_device_mappings {
    device_name = "/dev/sdb"
    delete_on_termination = true
    volume_type = "gp3"
    volume_size = 100
  }
}

build {
  name    = "build-gha-runner"
  sources = [
    "source.amazon-ebs.ubuntu"
  ]
  provisioner "shell" {
    script = "./scripts/init-runner.sh"
  }
}
