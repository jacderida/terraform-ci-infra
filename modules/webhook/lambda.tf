data "aws_iam_role" "webhook_lambda" {
  name = var.lambda_iam_role
}

resource "aws_lambda_function" "webhook" {
  filename          = var.webhook_file_path
  function_name     = "gha-runner-webhook"
  role              = data.aws_iam_role.webhook_lambda.arn
  handler           = "index.githubWebhook"
  runtime           = var.lambda_runtime
  timeout           = var.lambda_timeout
  architectures     = [var.lambda_architecture]

  environment {
    variables = {
      SQS_URL_WEBHOOK        = var.sqs_build_queue.id
      SQS_WORKFLOW_JOB_QUEUE = var.sqs_workflow_job_queue.id
      WEBHOOK_SECRET         = "blah"
    }
  }
}

resource "aws_lambda_permission" "webhook" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.webhook.execution_arn}/*/*/gha-runner-webhook"
}

resource "aws_iam_role_policy" "webhook_sqs" {
  name = "gha-runner-lambda-webhook-publish-sqs"
  role = data.aws_iam_role.webhook_lambda.name

  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["sqs:SendMessage", "sqs:GetQueueAttributes"],
        "Resource": "${var.sqs_build_queue.arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy" "webhook_workflow_job_sqs" {
  name = "gha-runner-lambda-webhook-publish-workflow-job-sqs"
  role = data.aws_iam_role.webhook_lambda.name

  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["sqs:SendMessage", "sqs:GetQueueAttributes"],
        "Resource": "${var.sqs_workflow_job_queue.arn}"
      }
    ]
  })
}
