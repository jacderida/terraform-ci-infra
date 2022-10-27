output "subnet_name" {
  value = module.vpc.public_subnets
}

output "gha_runner_security_group_name" {
  value = aws_security_group.gha_runner_image_builder.id
}
