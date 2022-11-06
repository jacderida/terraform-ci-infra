output "subnet_name" {
  value = module.vpc.public_subnets
}

output "gha_runner_security_group_name" {
  value = aws_security_group.gha_runner_image_builder.id
}

output "gha_runner_create_instance_repository_url" {
  value = aws_ecr_repository.gha_runner_create_instance.repository_url
}

output "gha_runner_terminate_instance_repository_url" {
  value = aws_ecr_repository.gha_runner_terminate_instance.repository_url
}
