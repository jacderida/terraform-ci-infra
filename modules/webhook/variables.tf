variable "lambda_iam_role" {
  type        = string
  default     = "gha-runner-lambda"
}

variable "lambda_runtime" {
  type        = string
  default     = "nodejs16.x"
}

variable "lambda_architecture" {
  type        = string
  default     = "x86_64"
}

variable "lambda_timeout" {
  type        = number
  default     = 10
}

variable "webhook_file_path" {
  type        = string
  default     = "webhook.zip"
}

variable "sqs_build_queue" {
  description = "SQS queue to publish accepted build events"
  type = object({
    id  = string
    arn = string
  })
}

variable "sqs_workflow_job_queue" {
  description = "SQS queue to monitor github events"
  type = object({
    id  = string
    arn = string
  })
  default = null
}
