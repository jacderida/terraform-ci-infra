resource "aws_apigatewayv2_api" "webhook" {
  name          = "github-action-webhook"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_route" "webhook" {
  api_id    = aws_apigatewayv2_api.webhook.id
  route_key = "POST /webhook"
  target    = "integrations/${aws_apigatewayv2_integration.webhook.id}"
}

resource "aws_apigatewayv2_stage" "webhook" {
  lifecycle {
    ignore_changes = [
      // see bug https://github.com/terraform-providers/terraform-provider-aws/issues/12893
      default_route_settings,
      // not terraform managed
      deployment_id
    ]
  }

  api_id      = aws_apigatewayv2_api.webhook.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "webhook" {
  lifecycle {
    ignore_changes = [
      // not terraform managed
      passthrough_behavior
    ]
  }

  api_id             = aws_apigatewayv2_api.webhook.id
  integration_type   = "AWS_PROXY"
  connection_type    = "INTERNET"
  description        = "GitHub App webhook for receiving build events"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.webhook.invoke_arn
}
