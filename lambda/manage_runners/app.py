import base64
import boto3
import hmac
import hashlib
import json
import jwt
import logging
import os
import requests
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# The EC2 infrastructure executes the user data script as the root user and you
# don't have any control over that. However, the runner configuration doesn't
# allow execution as root, but you *do* need to install and start the service as
# root. Hence, a bunch of commands execute as the ubuntu user, then we switch
# back to root. The directory switches to the home directory are necessary.
# The registration token will be supplied before the script is passed to the
# RunInstances API.
USER_DATA_SCRIPT = """#!/bin/bash

output=$(file -b -s /dev/nvme1n1)
until [ "$output" == "data" ]
do
    echo "$output"
    echo "disk still not mounted..."
    output=$(file -b -s /dev/nvme1n1)
done
mkfs -t ext4 /dev/nvme1n1
mkdir /mnt/data
mount /dev/nvme1n1 /mnt/data

mkdir /mnt/data/tmp
chmod 0777 /mnt/data/tmp

mkdir /mnt/data/runner
chown ubuntu:ubuntu /mnt/data/runner

mkdir /mnt/data/cargo
chown ubuntu:ubuntu /mnt/data/cargo
echo "CARGO_HOME=/mnt/data/cargo" >> /etc/environment

su ubuntu <<'EOF'
cd /home/ubuntu
REGISTRATION_TOKEN="__REGISTRATION_TOKEN__"
RUNNER_BASE_URL="https://github.com/actions/runner/releases/download"
RUNNER_VERSION="v2.317.0"
RUNNER_ARCHIVE_NAME="actions-runner-linux-x64-2.317.0.tar.gz"
SAFE_NETWORK_REPO_URL="https://github.com/maidsafe/safe_network"

cd /mnt/data/runner
mkdir actions-runner && cd actions-runner
curl -O -L ${RUNNER_BASE_URL}/${RUNNER_VERSION}/${RUNNER_ARCHIVE_NAME}

tar xvf ${RUNNER_ARCHIVE_NAME}
./config.sh --unattended \
  --url "${SAFE_NETWORK_REPO_URL}" --token "${REGISTRATION_TOKEN}" --labels self-hosted
EOF
(
    cd /mnt/data/runner/actions-runner
    ./svc.sh install ubuntu
    ./svc.sh start
)
"""
SIGNATURE_HEADER = "X-Hub-Signature-256"


class ConfigurationError(Exception):
    pass


def get_installed_app_token():
    """
    Gets a token for the installed Github App, which can then be used for the APIs that require it,
    such as requesting a registration token for a runner.

    The Github documentation outlines the full process:
    https://docs.github.com/en/developers/apps/building-github-apps/authenticating-with-github-apps#authenticating-as-a-github-app

    The summary is:
    * Use the private key registered with the runner app installed on the organisation to generate
      a JWT. Github requires sending an issue time and an expiry time for the token. The minus 60
      seconds is for "clock drift."
    * Authenticate with that token to get the app installation ID.
    * Make another request with the installation ID and the same JWT to get an access token.

    The private key is a PEM, but it's assigned to an environment variable as a base64-encoded
    string without any newline characters, to avoid any issues with that. We can't read it from a
    file because this code is executing in the context of a Lambda function.
    """
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise ConfigurationError("The GITHUB_APP_ID variable must be set")
    private_key_base64 = os.getenv("GITHUB_APP_PRIVATE_KEY_BASE64")
    if not private_key_base64:
        raise ConfigurationError(
            "The GITHUB_APP_PRIVATE_KEY_BASE64 variable must be set"
        )
    private_key = base64.b64decode(private_key_base64).decode("ascii")

    iat = int(time.time()) - 60
    exp = int(time.time()) + (10 * 60)
    payload = {"iat": iat, "exp": exp, "iss": int(app_id)}
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get("https://api.github.com/app/installations", headers=headers)
    if response.status_code != 200:
        logger.debug("Received unexpected response when requesting installation ID")
        logger.debug(f"status_code: {response.status_code}")
        logger.debug(f"text: {response.text}")
        raise ConfigurationError("Unexpected response indicates configuration issue")
    json = response.json()
    installation_id = json[0]["id"]

    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers,
    )
    json = response.json()
    token = json["token"]
    return token


def get_registration_token():
    token = get_installed_app_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(
        "https://api.github.com/repos/maidsafe/safe_network/actions/runners/registration-token",
        headers=headers,
    )
    json = response.json()
    registration_token = json["token"]
    return registration_token


def get_idle_runners():
    token = get_installed_app_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(
        "https://api.github.com/repos/maidsafe/safe_network/actions/runners",
        headers=headers,
    )
    json = response.json()
    return [(x["id"], x["name"]) for x in json["runners"] if x["busy"] == False]


def remove_runner(id):
    # The `workflow_job` event may have been received very quickly.
    # Therefore, sleep for a few seconds in case it takes some time to be marked as idle.
    time.sleep(3)
    token = get_installed_app_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.delete(
        f"https://api.github.com/repos/maidsafe/safe_network/actions/runners/{id}",
        headers=headers,
    )
    return response.status_code


def get_user_data_script(registration_token):
    # This is only really in its own function for testing purposes.
    # You can 'spy' on it and check the return value.
    user_data_script_with_token = USER_DATA_SCRIPT.replace(
        "__REGISTRATION_TOKEN__", registration_token
    )
    return user_data_script_with_token


def validate_env_vars():
    ami_id = os.getenv("AMI_ID")
    if not ami_id:
        raise ConfigurationError("The AMI_ID variable must be set")
    iam_instance_profile = os.getenv("EC2_IAM_INSTANCE_PROFILE")
    if not iam_instance_profile:
        raise ConfigurationError("The EC2_IAM_INSTANCE_PROFILE variable must be set")
    instance_type = os.getenv("EC2_INSTANCE_TYPE")
    if not instance_type:
        raise ConfigurationError("The EC2_INSTANCE_TYPE variable must be set")
    key_name = os.getenv("EC2_KEY_NAME")
    if not key_name:
        raise ConfigurationError("The EC2_KEY_NAME variable must be set")
    security_group_id = os.getenv("EC2_SECURITY_GROUP_ID")
    if not security_group_id:
        raise ConfigurationError("The EC2_SECURITY_GROUP_ID variable must be set")
    subnet_id = os.getenv("EC2_VPC_SUBNET_ID")
    if not subnet_id:
        raise ConfigurationError("The EC2_VPC_SUBNET_ID variable must be set")
    return (
        ami_id,
        iam_instance_profile,
        instance_type,
        key_name,
        security_group_id,
        subnet_id,
    )


def is_signature_valid(signature, payload):
    secret = os.getenv("GITHUB_APP_SECRET")
    if not secret:
        raise ConfigurationError("The GITHUB_APP_SECRET variable must be set")
    hmac_gen = hmac.new(secret.encode(), payload.encode(), hashlib.sha256)
    digest = "sha256=" + hmac_gen.hexdigest()
    return hmac.compare_digest(digest, signature)


def manage_runners(event, context):
    request_headers = event["headers"]
    if SIGNATURE_HEADER not in request_headers:
        logger.debug("The request did not contain the signature header")
        return {
            "statusCode": 400,
            "body": "The request did not contain the signature header",
        }
    signature = event["headers"][SIGNATURE_HEADER]
    if not is_signature_valid(signature, event["body"]):
        logger.debug("Signature received is not valid")
        return {"statusCode": 401, "body": "Signature received is not valid"}
    workflow_job = json.loads(event["body"])
    action = workflow_job["action"]
    logger.debug(f"Received workflow_job with {action} action")
    if action == "in_progress":
        logger.debug(
            "A workflow_job with an `in_progress` action will not be processed"
        )
        return {
            "statusCode": 200,
            "body": "A workflow_job with an `in_progress` action will not be processed",
        }
    if "self-hosted" not in workflow_job["workflow_job"]["labels"]:
        logger.debug("An EC2 instance will only be launched for a self-hosted job")
        return {
            "statusCode": 200,
            "body": "An EC2 instance will only be launched for a self-hosted job",
        }

    response = {}
    client = boto3.client("ec2")
    if action == "queued":
        (
            ami_id,
            iam_instance_profile,
            instance_type,
            key_name,
            security_group_id,
            subnet_id,
        ) = validate_env_vars()
        registration_token = get_registration_token()
        user_data_script_with_token = get_user_data_script(registration_token)
        response = client.run_instances(
            IamInstanceProfile={"Arn": iam_instance_profile},
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            UserData=user_data_script_with_token,
        )
        instance_id = response["Instances"][0]["InstanceId"]
        logger.debug(f"Launched EC2 instance with ID {instance_id}")
        response = {
            "statusCode": 201,
            "body": json.dumps(
                {
                    "instance_id": instance_id,
                }
            ),
        }
    elif action == "completed":
        idle_runners = get_idle_runners()
        ec2_response = client.describe_instances()
        instance_ids = []
        for (runner_id, private_ip) in idle_runners:
            for reservation in ec2_response["Reservations"]:
                for instance in reservation["Instances"]:
                    if instance["PrivateDnsName"].startswith(private_ip):
                        instance_id = instance["InstanceId"]
                        instance_ids.append(instance_id)
        for (runner_id, private_ip) in idle_runners:
            logger.debug(f"Will remove idle runner {private_ip}")
            remove_runner(runner_id)
        logger.debug(f"Will terminate instances with IDs {instance_ids}")
        client.terminate_instances(InstanceIds=instance_ids)
        response = {"statusCode": 201, "TerminatedInstanceIds": instance_ids}
    return response
