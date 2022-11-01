SHELL:=/bin/bash

infrastructure:
	(
		cd lambda/webhook
		yarn install
		yarn run test
		yarn dist
	)
	terraform init
	terraform apply -auto-approve

.ONESHELL:
build-image:
	security_group_id=$$(terraform output -raw gha_runner_security_group_name | xargs)
	subnet_id=$$(terraform output subnet_name | xargs | awk '{ print $$2 }' | sed s/,//)
	packer init .
	packer build -var="security_group_id=$$security_group_id" \
		-var="subnet_id=$$subnet_id" gha-runner.pkr.hcl
