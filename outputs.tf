output "subnet_name" {
  value = module.vpc.public_subnets
}

output "gha_runner_security_group_name" {
  value = aws_security_group.gha_runner.id
}

output "gha_runner_image_builder_security_group_name" {
  value = aws_security_group.gha_runner_image_builder.id
}

output "manage_runners_repository_url" {
  value = aws_ecr_repository.manage_runners.repository_url
}
