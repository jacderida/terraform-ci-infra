import datetime
import hmac
import hashlib
import os
import pytest

from dateutil.tz import tzutc
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


@pytest.fixture()
def describe_instances_response():
    return {
        "Reservations": [
            {
                "Groups": [],
                "Instances": [
                    {
                        "AmiLaunchIndex": 0,
                        "ImageId": "ami-05b371382b07cb80a",
                        "InstanceId": "i-0d63d1911b0c34cf7",
                        "InstanceType": "t2.medium",
                        "KeyName": "gha_runner_image_builder",
                        "LaunchTime": datetime.datetime(
                            2022, 11, 16, 15, 29, 38, tzinfo=tzutc()
                        ),
                        "Monitoring": {"State": "disabled"},
                        "Placement": {
                            "AvailabilityZone": "eu-west-2a",
                            "GroupName": "",
                            "Tenancy": "default",
                        },
                        "PrivateDnsName": "ip-10-0-0-128.eu-west-2.compute.internal",
                        "PrivateIpAddress": "10.0.0.128",
                        "ProductCodes": [],
                        "PublicDnsName": "",
                        "PublicIpAddress": "3.9.180.215",
                        "State": {"Code": 16, "Name": "running"},
                        "StateTransitionReason": "",
                        "SubnetId": "subnet-08486e3b32f903438",
                        "VpcId": "vpc-0571e788c4263aeb3",
                        "Architecture": "x86_64",
                        "BlockDeviceMappings": [
                            {
                                "DeviceName": "/dev/sda1",
                                "Ebs": {
                                    "AttachTime": datetime.datetime(
                                        2022, 11, 16, 15, 29, 38, tzinfo=tzutc()
                                    ),
                                    "DeleteOnTermination": True,
                                    "Status": "attached",
                                    "VolumeId": "vol-06318a4cc96429a43",
                                },
                            }
                        ],
                        "ClientToken": "2bee577c-e078-438d-bfdf-720468f9f564",
                        "EbsOptimized": False,
                        "EnaSupport": True,
                        "Hypervisor": "xen",
                        "NetworkInterfaces": [
                            {
                                "Association": {
                                    "IpOwnerId": "amazon",
                                    "PublicDnsName": "",
                                    "PublicIp": "3.9.180.215",
                                },
                                "Attachment": {
                                    "AttachTime": datetime.datetime(
                                        2022, 11, 16, 15, 29, 38, tzinfo=tzutc()
                                    ),
                                    "AttachmentId": "eni-attach-043aa5db24f41c29f",
                                    "DeleteOnTermination": True,
                                    "DeviceIndex": 0,
                                    "Status": "attached",
                                    "NetworkCardIndex": 0,
                                },
                                "Description": "",
                                "Groups": [
                                    {
                                        "GroupName": "gha_runner_image_builder",
                                        "GroupId": "sg-0f802f984aa514480",
                                    }
                                ],
                                "Ipv6Addresses": [],
                                "MacAddress": "06:7f:c2:a3:79:9e",
                                "NetworkInterfaceId": "eni-04a15d49979939d56",
                                "OwnerId": "389640522532",
                                "PrivateIpAddress": "10.0.0.128",
                                "PrivateIpAddresses": [
                                    {
                                        "Association": {
                                            "IpOwnerId": "amazon",
                                            "PublicDnsName": "",
                                            "PublicIp": "3.9.180.215",
                                        },
                                        "Primary": True,
                                        "PrivateIpAddress": "10.0.0.128",
                                    }
                                ],
                                "SourceDestCheck": True,
                                "Status": "in-use",
                                "SubnetId": "subnet-08486e3b32f903438",
                                "VpcId": "vpc-0571e788c4263aeb3",
                                "InterfaceType": "interface",
                            }
                        ],
                        "RootDeviceName": "/dev/sda1",
                        "RootDeviceType": "ebs",
                        "SecurityGroups": [
                            {
                                "GroupName": "gha_runner_image_builder",
                                "GroupId": "sg-0f802f984aa514480",
                            }
                        ],
                        "SourceDestCheck": True,
                        "VirtualizationType": "hvm",
                        "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
                        "CapacityReservationSpecification": {
                            "CapacityReservationPreference": "open"
                        },
                        "HibernationOptions": {"Configured": False},
                        "MetadataOptions": {
                            "State": "applied",
                            "HttpTokens": "optional",
                            "HttpPutResponseHopLimit": 1,
                            "HttpEndpoint": "enabled",
                            "HttpProtocolIpv6": "disabled",
                            "InstanceMetadataTags": "disabled",
                        },
                        "EnclaveOptions": {"Enabled": False},
                        "PlatformDetails": "Linux/UNIX",
                        "UsageOperation": "RunInstances",
                        "UsageOperationUpdateTime": datetime.datetime(
                            2022, 11, 16, 15, 29, 38, tzinfo=tzutc()
                        ),
                        "PrivateDnsNameOptions": {
                            "HostnameType": "ip-name",
                            "EnableResourceNameDnsARecord": False,
                            "EnableResourceNameDnsAAAARecord": False,
                        },
                        "MaintenanceOptions": {"AutoRecovery": "default"},
                    }
                ],
                "OwnerId": "389640522532",
                "ReservationId": "r-079ac49c9238b5903",
            },
            {
                "Groups": [],
                "Instances": [
                    {
                        "AmiLaunchIndex": 0,
                        "ImageId": "ami-05b371382b07cb80a",
                        "InstanceId": "i-0462bd6a044280798",
                        "InstanceType": "t2.medium",
                        "KeyName": "gha_runner_image_builder",
                        "LaunchTime": datetime.datetime(
                            2022, 11, 16, 15, 30, 2, tzinfo=tzutc()
                        ),
                        "Monitoring": {"State": "disabled"},
                        "Placement": {
                            "AvailabilityZone": "eu-west-2a",
                            "GroupName": "",
                            "Tenancy": "default",
                        },
                        "PrivateDnsName": "ip-10-0-0-211.eu-west-2.compute.internal",
                        "PrivateIpAddress": "10.0.0.211",
                        "ProductCodes": [],
                        "PublicDnsName": "",
                        "PublicIpAddress": "13.40.178.114",
                        "State": {"Code": 16, "Name": "running"},
                        "StateTransitionReason": "",
                        "SubnetId": "subnet-08486e3b32f903438",
                        "VpcId": "vpc-0571e788c4263aeb3",
                        "Architecture": "x86_64",
                        "BlockDeviceMappings": [
                            {
                                "DeviceName": "/dev/sda1",
                                "Ebs": {
                                    "AttachTime": datetime.datetime(
                                        2022, 11, 16, 15, 30, 2, tzinfo=tzutc()
                                    ),
                                    "DeleteOnTermination": True,
                                    "Status": "attached",
                                    "VolumeId": "vol-0a570751e897807f7",
                                },
                            }
                        ],
                        "ClientToken": "6a5062cd-69a7-4eea-8b76-94d4319ccb9c",
                        "EbsOptimized": False,
                        "EnaSupport": True,
                        "Hypervisor": "xen",
                        "NetworkInterfaces": [
                            {
                                "Association": {
                                    "IpOwnerId": "amazon",
                                    "PublicDnsName": "",
                                    "PublicIp": "13.40.178.114",
                                },
                                "Attachment": {
                                    "AttachTime": datetime.datetime(
                                        2022, 11, 16, 15, 30, 2, tzinfo=tzutc()
                                    ),
                                    "AttachmentId": "eni-attach-059ae5ff374bfab6e",
                                    "DeleteOnTermination": True,
                                    "DeviceIndex": 0,
                                    "Status": "attached",
                                    "NetworkCardIndex": 0,
                                },
                                "Description": "",
                                "Groups": [
                                    {
                                        "GroupName": "gha_runner_image_builder",
                                        "GroupId": "sg-0f802f984aa514480",
                                    }
                                ],
                                "Ipv6Addresses": [],
                                "MacAddress": "06:90:a4:9a:68:cc",
                                "NetworkInterfaceId": "eni-09b544ec73b766acc",
                                "OwnerId": "389640522532",
                                "PrivateIpAddress": "10.0.0.211",
                                "PrivateIpAddresses": [
                                    {
                                        "Association": {
                                            "IpOwnerId": "amazon",
                                            "PublicDnsName": "",
                                            "PublicIp": "13.40.178.114",
                                        },
                                        "Primary": True,
                                        "PrivateIpAddress": "10.0.0.211",
                                    }
                                ],
                                "SourceDestCheck": True,
                                "Status": "in-use",
                                "SubnetId": "subnet-08486e3b32f903438",
                                "VpcId": "vpc-0571e788c4263aeb3",
                                "InterfaceType": "interface",
                            }
                        ],
                        "RootDeviceName": "/dev/sda1",
                        "RootDeviceType": "ebs",
                        "SecurityGroups": [
                            {
                                "GroupName": "gha_runner_image_builder",
                                "GroupId": "sg-0f802f984aa514480",
                            }
                        ],
                        "SourceDestCheck": True,
                        "VirtualizationType": "hvm",
                        "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
                        "CapacityReservationSpecification": {
                            "CapacityReservationPreference": "open"
                        },
                        "HibernationOptions": {"Configured": False},
                        "MetadataOptions": {
                            "State": "applied",
                            "HttpTokens": "optional",
                            "HttpPutResponseHopLimit": 1,
                            "HttpEndpoint": "enabled",
                            "HttpProtocolIpv6": "disabled",
                            "InstanceMetadataTags": "disabled",
                        },
                        "EnclaveOptions": {"Enabled": False},
                        "PlatformDetails": "Linux/UNIX",
                        "UsageOperation": "RunInstances",
                        "UsageOperationUpdateTime": datetime.datetime(
                            2022, 11, 16, 15, 30, 2, tzinfo=tzutc()
                        ),
                        "PrivateDnsNameOptions": {
                            "HostnameType": "ip-name",
                            "EnableResourceNameDnsARecord": False,
                            "EnableResourceNameDnsAAAARecord": False,
                        },
                        "MaintenanceOptions": {"AutoRecovery": "default"},
                    }
                ],
                "OwnerId": "389640522532",
                "ReservationId": "r-08184d3d1061e282d",
            },
        ],
        "ResponseMetadata": {
            "RequestId": "0890266c-21c4-4e3f-b91c-dd90ac590cbe",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "0890266c-21c4-4e3f-b91c-dd90ac590cbe",
                "cache-control": "no-cache, no-store",
                "strict-transport-security": "max-age=31536000; includeSubDomains",
                "vary": "accept-encoding",
                "content-type": "text/xml;charset=UTF-8",
                "transfer-encoding": "chunked",
                "date": "Wed, 16 Nov 2022 15:57:57 GMT",
                "server": "AmazonEC2",
            },
            "RetryAttempts": 0,
        },
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
def test_manage_runners_with_queued_job_integration(
    apigw_event, workflow_job_webhook_payload
):
    """
    An integration test that can be used for debugging.

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

    pytest tests/integration
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


@pytest.mark.skip(reason="full integration test for debugging")
def test_manage_runners_with_completed_job_integration(
    apigw_event, workflow_job_webhook_payload
):
    """
    An integration test that can be used for debugging.

    To run it, set all the environment variables to the values used in the real
    environment. You also need to supply the keys of an AWS user who has
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

    pytest tests/integration
    """
    github_app_secret = os.getenv("GITHUB_APP_SECRET")
    if not github_app_secret:
        raise ConfigurationError("The GITHUB_APP_SECRET variable must be set")
    payload_with_different_action = workflow_job_webhook_payload.replace(
        "queued", "completed"
    )
    apigw_event["body"] = payload_with_different_action
    apigw_event["headers"]["X-Hub-Signature-256"] = generate_signature(
        github_app_secret.encode(), payload_with_different_action.encode()
    )
    response = app.manage_runners(apigw_event, "")
    print(response)
