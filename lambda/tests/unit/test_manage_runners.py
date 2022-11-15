import hmac
import hashlib
import json
import os
import pytest

from manage_runners import app
from manage_runners.app import ConfigurationError


TEST_SECRET = "GLoA096eDGlXXF5SiCEq"


@pytest.fixture()
def workflow_job_webhook_payload():
    """
    Example defined here:
    https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#workflow_job

    The `action` has been changed from `in_progress` to `queued` because we'll be interested in
    queued actions; we'll only launch an EC2 instance for a `queued` action.

    This workflow_job payload will be the body of the HTTP request received by the Lambda.
    """
    return """{
  "action": "queued",
  "workflow_job": {
    "id": 2832853555,
    "run_id": 940463255,
    "run_url": "https://api.github.com/repos/octo-org/example-workflow/actions/runs/940463255",
    "node_id": "MDg6Q2hlY2tSdW4yODMyODUzNT55",
    "head_sha": "e3103f8eb03e1ad7f2331c5446b23c070fc54055",
    "url": "https://api.github.com/repos/octo-org/example-workflow/actions/jobs/2832853555",
    "html_url": "https://github.com/octo-org/example-workflow/runs/2832853555",
    "status": "in_progress",
    "conclusion": null,
    "started_at": "2021-06-15T19:22:27Z",
    "completed_at": null,
    "name": "Test workflow",
    "steps": [
      {
        "name": "Set up job",
        "status": "in_progress",
        "conclusion": null,
        "number": 1,
        "started_at": "2021-06-15T19:22:27.000Z",
        "completed_at": null
      }
    ],
    "check_run_url": "https://api.github.com/repos/octo-org/example-workflow/check-runs/2832853555",
    "labels": ["self-hosted"],
    "runner_id": 1,
    "runner_name": "my runner",
    "runner_group_id": 2,
    "runner_group_name": "my runner group"
  },
  "repository": {
    "id": 376034443,
    "node_id": "MDEwOlJlcG9zaXRvcnkzNzYwMzQ0ND55",
    "name": "example-workflow",
    "full_name": "octo-org/example-workflow",
    "private": true,
    "owner": {
      "login": "octo-org",
      "id": 33435655,
      "node_id": "MDEyOk9yZ2FuaXphdGlvbjMzNDM1Nj55",
      "avatar_url": "https://avatars.githubusercontent.com/u/21031067?s=460&u=d851e01410b4f1674f000ba7e0dc94e0b82cd9cc&v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/octo-org",
      "html_url": "https://github.com/octo-org",
      "followers_url": "https://api.github.com/users/octo-org/followers",
      "following_url": "https://api.github.com/users/octo-org/following{/other_user}",
      "gists_url": "https://api.github.com/users/octo-org/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/octo-org/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/octo-org/subscriptions",
      "organizations_url": "https://api.github.com/users/octo-org/orgs",
      "repos_url": "https://api.github.com/users/octo-org/repos",
      "events_url": "https://api.github.com/users/octo-org/events{/privacy}",
      "received_events_url": "https://api.github.com/users/octo-org/received_events",
      "type": "Organization",
      "site_admin": false
    },
    "html_url": "https://github.com/octo-org/example-workflow",
    "description": "Test workflow",
    "fork": false,
    "url": "https://api.github.com/repos/octo-org/example-workflow",
    "forks_url": "https://api.github.com/repos/octo-org/example-workflow/forks",
    "keys_url": "https://api.github.com/repos/octo-org/example-workflow/keys{/key_id}",
    "collaborators_url": "https://api.github.com/repos/octo-org/example-workflow/collaborators{/collaborator}",
    "teams_url": "https://api.github.com/repos/octo-org/example-workflow/teams",
    "hooks_url": "https://api.github.com/repos/octo-org/example-workflow/hooks",
    "issue_events_url": "https://api.github.com/repos/octo-org/example-workflow/issues/events{/number}",
    "events_url": "https://api.github.com/repos/octo-org/example-workflow/events",
    "assignees_url": "https://api.github.com/repos/octo-org/example-workflow/assignees{/user}",
    "branches_url": "https://api.github.com/repos/octo-org/example-workflow/branches{/branch}",
    "tags_url": "https://api.github.com/repos/octo-org/example-workflow/tags",
    "blobs_url": "https://api.github.com/repos/octo-org/example-workflow/git/blobs{/sha}",
    "git_tags_url": "https://api.github.com/repos/octo-org/example-workflow/git/tags{/sha}",
    "git_refs_url": "https://api.github.com/repos/octo-org/example-workflow/git/refs{/sha}",
    "trees_url": "https://api.github.com/repos/octo-org/example-workflow/git/trees{/sha}",
    "statuses_url": "https://api.github.com/repos/octo-org/example-workflow/statuses/{sha}",
    "languages_url": "https://api.github.com/repos/octo-org/example-workflow/languages",
    "stargazers_url": "https://api.github.com/repos/octo-org/example-workflow/stargazers",
    "contributors_url": "https://api.github.com/repos/octo-org/example-workflow/contributors",
    "subscribers_url": "https://api.github.com/repos/octo-org/example-workflow/subscribers",
    "subscription_url": "https://api.github.com/repos/octo-org/example-workflow/subscription",
    "commits_url": "https://api.github.com/repos/octo-org/example-workflow/commits{/sha}",
    "git_commits_url": "https://api.github.com/repos/octo-org/example-workflow/git/commits{/sha}",
    "comments_url": "https://api.github.com/repos/octo-org/example-workflow/comments{/number}",
    "issue_comment_url": "https://api.github.com/repos/octo-org/example-workflow/issues/comments{/number}",
    "contents_url": "https://api.github.com/repos/octo-org/example-workflow/contents/{+path}",
    "compare_url": "https://api.github.com/repos/octo-org/example-workflow/compare/{base}...{head}",
    "merges_url": "https://api.github.com/repos/octo-org/example-workflow/merges",
    "archive_url": "https://api.github.com/repos/octo-org/example-workflow/{archive_format}{/ref}",
    "downloads_url": "https://api.github.com/repos/octo-org/example-workflow/downloads",
    "issues_url": "https://api.github.com/repos/octo-org/example-workflow/issues{/number}",
    "pulls_url": "https://api.github.com/repos/octo-org/example-workflow/pulls{/number}",
    "milestones_url": "https://api.github.com/repos/octo-org/example-workflow/milestones{/number}",
    "notifications_url": "https://api.github.com/repos/octo-org/example-workflow/notifications{?since,all,participating}",
    "labels_url": "https://api.github.com/repos/octo-org/example-workflow/labels{/name}",
    "releases_url": "https://api.github.com/repos/octo-org/example-workflow/releases{/id}",
    "deployments_url": "https://api.github.com/repos/octo-org/example-workflow/deployments",
    "created_at": "2021-06-11T13:29:13Z",
    "updated_at": "2021-06-11T13:33:01Z",
    "pushed_at": "2021-06-11T13:32:58Z",
    "git_url": "git://github.com/octo-org/example-workflow.git",
    "ssh_url": "git@github.com:octo-org/example-workflow.git",
    "clone_url": "https://github.com/octo-org/example-workflow.git",
    "svn_url": "https://github.com/octo-org/example-workflow",
    "homepage": null,
    "size": 1,
    "stargazers_count": 0,
    "watchers_count": 0,
    "language": null,
    "has_issues": true,
    "has_projects": true,
    "has_downloads": true,
    "has_wiki": true,
    "has_pages": false,
    "forks_count": 0,
    "mirror_url": null,
    "archived": false,
    "disabled": false,
    "open_issues_count": 0,
    "license": null,
    "forks": 0,
    "open_issues": 0,
    "watchers": 0,
    "default_branch": "main"
  },
  "organization": {
    "login": "octo-org",
    "id": 33435655,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjMzNDM1Nj55",
    "url": "https://api.github.com/orgs/octo-org",
    "repos_url": "https://api.github.com/orgs/octo-org/repos",
    "events_url": "https://api.github.com/orgs/octo-org/events",
    "hooks_url": "https://api.github.com/orgs/octo-org/hooks",
    "issues_url": "https://api.github.com/orgs/octo-org/issues",
    "members_url": "https://api.github.com/orgs/octo-org/members{/member}",
    "public_members_url": "https://api.github.com/orgs/octo-org/public_members{/member}",
    "avatar_url": "https://avatars.githubusercontent.com/u/21031067?s=460&u=d851e01410b4f1674f000ba7e0dc94e0b82cd9cc&v=4",
    "description": "octo-org"
  },
  "sender": {
    "login": "octocat",
    "id": 319655,
    "node_id": "MDQ6VXNlcjMxOTY1NQ55",
    "avatar_url": "https://avatars.githubusercontent.com/u/21031067?s=460&u=d851e01410b4f1674f000ba7e0dc94e0b82cd9cc&v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/octocat",
    "html_url": "https://github.com/octocat",
    "followers_url": "https://api.github.com/users/octocat/followers",
    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
    "organizations_url": "https://api.github.com/users/octocat/orgs",
    "repos_url": "https://api.github.com/users/octocat/repos",
    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
    "received_events_url": "https://api.github.com/users/octocat/received_events",
    "type": "User",
    "site_admin": true
  }
}"""


@pytest.fixture()
def apigw_event():
    """Generates API GW Event"""

    return {
        "body": "",
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


def generate_signature(secret, payload):
    """
    See the Github documentation here:
    https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks#validating-payloads-from-github

    Github send the signature in a `X-Hub-Signature-256` header. It's a hash of the workflow_job
    payload, using the secret that's defined on the Github app. We use a fake secret here. When the
    Lambda is deployed the `GITHUB_APP_SECRET` environment variable will be set to the real secret.
    """
    hmac_gen = hmac.new(secret, payload, hashlib.sha256)
    digest = "sha256=" + hmac_gen.hexdigest()
    return digest


@pytest.mark.skip(reason="full integration test for debugging")
def test_manage_runners_integration(apigw_event, workflow_job_webhook_payload):
    """
    A full integration test that can be used for debugging.

    To run it, remove the skip and set all the environment variables to the values used in
    the real environment. You also need to supply the keys of an AWS user who has
    permission to run instances. For example:

    export AWS_ACCESS_KEY_ID=<access key id>
    export AWS_SECRET_ACCESS_KEY=<secret access key>
    export AWS_DEFAULT_REGION=eu-west-2
    export AMI_ID=ami-05b371382b07cb80a
    export EC2_INSTANCE_TYPE=t2.medium
    export EC2_KEY_NAME=gha_runner_image_builder
    export EC2_SECURITY_GROUP_ID=sg-0f802f984aa514480
    export EC2_VPC_SUBNET_ID=subnet-08486e3b32f903438
    export GITHUB_APP_ID=<app id>
    export GITHUB_APP_PRIVATE_KEY_BASE64=<base64 encoded private key>
    export GITHUB_APP_SECRET=<app secret>

    pytest --capture=no --verbose -k test_manage_runners_integration tests/
    """
    github_app_secret = os.getenv("GITHUB_APP_SECRET")
    if not github_app_secret:
        raise ConfigurationError("The GITHUB_APP_SECRET variable must be set")
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        github_app_secret.encode(), workflow_job_webhook_payload.encode()
    )
    response = app.manage_runners(apigw_event, "")
    print(response)


def test_manage_runners(apigw_event, workflow_job_webhook_payload, mocker, monkeypatch):
    monkeypatch.setenv("AMI_ID", "ami-092fe15da02f3f1bg")
    monkeypatch.setenv("EC2_INSTANCE_TYPE", "t2.medium")
    monkeypatch.setenv("EC2_KEY_NAME", "gha_runner_image_builder")
    monkeypatch.setenv("EC2_SECURITY_GROUP_ID", "sg-0f802f984aa514480")
    monkeypatch.setenv("EC2_VPC_SUBNET_ID", "subnet-08486e3b32f903438")
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)

    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )

    boto_client_mock = mocker.patch("manage_runners.app.boto3.client")
    boto_client_mock.return_value.run_instances.return_value = {
        "Instances": [{"InstanceId": "i-123456"}]
    }
    registration_token_mock = mocker.patch("manage_runners.app.get_registration_token")
    registration_token_mock.return_value = "CuV2hw4Xtig5a8oYu1KL"
    spy = mocker.spy(app, "get_user_data_script")

    response = app.manage_runners(apigw_event, "")
    data = json.loads(response["body"])
    base64_encoded_user_data_script = spy.spy_return

    boto_client_mock.return_value.run_instances.assert_called_with(
        ImageId="ami-092fe15da02f3f1bg",
        InstanceType="t2.medium",
        KeyName="gha_runner_image_builder",
        MaxCount=1,
        MinCount=1,
        SecurityGroupIds=["sg-0f802f984aa514480"],
        SubnetId="subnet-08486e3b32f903438",
        UserData=base64_encoded_user_data_script,
    )
    assert response["statusCode"] == 201
    assert "instance_id" in response["body"]
    assert data["instance_id"] == "i-123456"


def test_manage_runners_with_in_progress_workflow_job_action(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)

    payload_with_different_action = workflow_job_webhook_payload.replace(
        "queued", "in_progress"
    )
    apigw_event["body"] = payload_with_different_action
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), payload_with_different_action.encode()
    )

    response = app.manage_runners(apigw_event, "")

    assert response["statusCode"] == 200
    assert (
        response["body"]
        == "A workflow_job with a in_progress action does not require a new EC2 instance"
    )


def test_manage_runners_with_completed_workflow_job_action(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)

    payload_with_different_action = workflow_job_webhook_payload.replace(
        "queued", "completed"
    )
    apigw_event["body"] = payload_with_different_action
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), payload_with_different_action.encode()
    )

    response = app.manage_runners(apigw_event, "")

    assert response["statusCode"] == 200
    assert (
        response["body"]
        == "A workflow_job with a completed action does not require a new EC2 instance"
    )


def test_manage_runners_with_non_self_hosted_label(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)

    payload_with_non_self_hosted = workflow_job_webhook_payload.replace(
        "self-hosted", "ubuntu-latest"
    )
    apigw_event["body"] = payload_with_non_self_hosted
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), payload_with_non_self_hosted.encode()
    )

    response = app.manage_runners(apigw_event, "")

    assert response["statusCode"] == 200
    assert (
        response["body"]
        == "An EC2 instance will only be launched for a self-hosted job"
    )


def test_manage_runners_sha256_sig_not_present(
    apigw_event, workflow_job_webhook_payload
):
    apigw_event["body"] = workflow_job_webhook_payload
    response = app.manage_runners(apigw_event, "")
    assert response["statusCode"] == 400
    assert response["body"] == "The request did not contain the signature header"


def test_manage_runners_sha256_sig_does_not_match(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        "another secret".encode(), workflow_job_webhook_payload.encode()
    )
    response = app.manage_runners(apigw_event, "")
    assert response["statusCode"] == 401
    assert response["body"] == "Signature received is not valid"


def test_manage_runners_github_secret_is_not_set(
    apigw_event, workflow_job_webhook_payload
):
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    with pytest.raises(
        ConfigurationError, match="The GITHUB_APP_SECRET variable must be set"
    ):
        app.manage_runners(apigw_event, "")


def test_manage_runners_ami_id_is_not_set(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    with pytest.raises(ConfigurationError, match="The AMI_ID variable must be set"):
        app.manage_runners(apigw_event, "")


def test_manage_runners_instance_type_is_not_set(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    monkeypatch.setenv("AMI_ID", "ami-092fe15da02f3f1bg")
    monkeypatch.setenv("EC2_KEY_NAME", "gha_runner_image_builder")
    monkeypatch.setenv("EC2_SECURITY_GROUP_ID", "sg-0f802f984aa514480")
    monkeypatch.setenv("EC2_VPC_SUBNET_ID", "subnet-08486e3b32f903438")
    with pytest.raises(
        ConfigurationError, match="The EC2_INSTANCE_TYPE variable must be set"
    ):
        app.manage_runners(apigw_event, "")


def test_manage_runners_key_name_is_not_set(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    monkeypatch.setenv("AMI_ID", "ami-092fe15da02f3f1bg")
    monkeypatch.setenv("EC2_INSTANCE_TYPE", "t2.medium")
    monkeypatch.setenv("EC2_SECURITY_GROUP_ID", "sg-0f802f984aa514480")
    monkeypatch.setenv("EC2_VPC_SUBNET_ID", "subnet-08486e3b32f903438")
    with pytest.raises(
        ConfigurationError, match="The EC2_KEY_NAME variable must be set"
    ):
        app.manage_runners(apigw_event, "")


def test_manage_runners_security_group_id_is_not_set(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    monkeypatch.setenv("AMI_ID", "ami-092fe15da02f3f1bg")
    monkeypatch.setenv("EC2_INSTANCE_TYPE", "t2.medium")
    monkeypatch.setenv("EC2_KEY_NAME", "gha_runner_image_builder")
    monkeypatch.setenv("EC2_VPC_SUBNET_ID", "subnet-08486e3b32f903438")
    with pytest.raises(
        ConfigurationError, match="The EC2_SECURITY_GROUP_ID variable must be set"
    ):
        app.manage_runners(apigw_event, "")


def test_manage_runners_subnet_id_is_not_set(
    apigw_event, workflow_job_webhook_payload, monkeypatch
):
    apigw_event["body"] = workflow_job_webhook_payload
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        TEST_SECRET.encode(), workflow_job_webhook_payload.encode()
    )
    monkeypatch.setenv("GITHUB_APP_SECRET", TEST_SECRET)
    monkeypatch.setenv("AMI_ID", "ami-092fe15da02f3f1bg")
    monkeypatch.setenv("EC2_INSTANCE_TYPE", "t2.medium")
    monkeypatch.setenv("EC2_KEY_NAME", "gha_runner_image_builder")
    monkeypatch.setenv("EC2_SECURITY_GROUP_ID", "sg-0f802f984aa514480")
    with pytest.raises(
        ConfigurationError, match="The EC2_VPC_SUBNET_ID variable must be set"
    ):
        app.manage_runners(apigw_event, "")
