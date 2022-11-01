variable "lambda_iam_role" {
  type        = string
  default     = "gha-runner-lambda"
}

variable "subnet_name" {
  default = "gha-runner"
  description = "The name for the subnet used in the VPC"
}

variable "availability_zones" {
  default = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  description = "The availability zones to use"
}

variable "gha_runner_security_group_name" {
  default = "gha_runner"
  description = "The name of the security group that GHA runner instances will launch into"
}

variable "gha_runner_image_security_group_name" {
  default = "gha_runner_image_builder"
  description = "The name of the security group for the instance for building the GHA runner AMI"
}

variable "gha_runner_image_builder_key_name" {
  default = "gha_runner_image_builder"
  description = "The name of the keypair required for building the GHA runner AMI"
}
