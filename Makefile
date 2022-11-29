SHELL := /bin/bash
REGISTRY_URI := dkr.ecr.eu-west-2.amazonaws.com
REPO_NAME := manage_runners
STACK_NAME := manage-runners
TAG_NAME := python3.9-v1

infrastructure:
	terraform init
	terraform apply -auto-approve -var-file=secrets.tfvars

.ONESHELL:
build-image:
	security_group_id=$$(terraform output -raw gha_runner_security_group_name | xargs)
	subnet_id=$$(terraform output subnet_name | xargs | awk '{ print $$2 }' | sed s/,//)
	packer init .
	packer build -var="security_group_id=$$security_group_id" \
		-var="subnet_id=$$subnet_id" gha-runner.pkr.hcl

deploy-create-instance-function:
	(
		cd lambda/manage_runners
		docker build \
			--tag $$AWS_ACCOUNT_NUMBER.${REGISTRY_URI}/${REPO_NAME}:${TAG_NAME} \
			.
	)
	docker push $$AWS_ACCOUNT_NUMBER.${REGISTRY_URI}/${REPO_NAME}:${TAG_NAME}
	(
		security_group_id=$$(terraform output -raw gha_runner_image_security_group_name | xargs)
		subnet_id=$$(terraform output subnet_name | xargs | awk '{ print $$2 }' | sed s/,//)
		cd lambda
		sam deploy \
			--stack-name ${STACK_NAME} \
			--template template.yaml \
			--resolve-image-repos \
			--s3-bucket maidsafe-ci-infra \
			--s3-prefix manage_runners_lambda \
			--parameter-overrides Ec2SecurityGroupId=$$security_group_id Ec2VpcSubnetId=$$subnet_id
	)

clean-create-instance-function:
	(
		cd lambda
		sam delete --stack-name ${STACK_NAME} --no-prompts --region eu-west-2
	)
