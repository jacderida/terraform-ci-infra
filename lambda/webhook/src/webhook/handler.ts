import { Webhooks } from '@octokit/webhooks';
import { CheckRunEvent, WorkflowJobEvent } from '@octokit/webhooks-types';
import { IncomingHttpHeaders } from 'http';

import { Response } from '../lambda';
import { sendActionRequest, sendWebhookEventToWorkflowJobQueue } from '../sqs';
import { LogFields, logger as rootLogger } from './logger';

const logger = rootLogger.getChildLogger();

export async function handle(headers: IncomingHttpHeaders, body: string): Promise<Response> {
  // ensure header keys lower case since github headers can contain capitals.
  for (const key in headers) {
    headers[key.toLowerCase()] = headers[key];
  }

  const githubEvent = headers['x-github-event'] as string;

  let response: Response = {
    statusCode: await verifySignature(githubEvent, headers, body),
  };

  if (response.statusCode != 200) {
    return response;
  }

  if (githubEvent != 'workflow_job') {
    logger.warn(`Unsupported event type.`, LogFields.print());
    return {
      statusCode: 202,
      body: `Ignoring unsupported event ${githubEvent}`,
    };
  }

  const payload = JSON.parse(body);
  LogFields.fields.event = githubEvent;
  LogFields.fields.repository = payload.repository.full_name;
  LogFields.fields.action = payload.action;
  LogFields.fields.name = payload[githubEvent].name;
  LogFields.fields.status = payload[githubEvent].status;
  LogFields.fields.workflowJobId = payload[githubEvent].id;
  LogFields.fields.started_at = payload[githubEvent]?.started_at;

  /*
  The app subscribes to all `check_run` and `workflow_job` events.
  If the event status is `completed`, log the data for workflow metrics.
  */
  LogFields.fields.completed_at = payload[githubEvent]?.completed_at;
  LogFields.fields.conclusion = payload[githubEvent]?.conclusion;

  logger.info(`Processing Github event`, LogFields.print());

  const workflowEventPayload = payload as WorkflowJobEvent;
  response = await handleWorkflowJob(
    workflowEventPayload,
    githubEvent,
  );
  await sendWorkflowJobEvents(githubEvent, workflowEventPayload);
  return response;
}

async function sendWorkflowJobEvents(githubEvent: string, workflowEventPayload: WorkflowJobEvent) {
  await sendWebhookEventToWorkflowJobQueue({
    workflowJobEvent: workflowEventPayload,
  });
}

async function verifySignature(
  githubEvent: string,
  headers: IncomingHttpHeaders,
  body: string,
): Promise<number> {
  let signature;
  if ('x-hub-signature-256' in headers) {
    signature = headers['x-hub-signature-256'] as string;
  } else {
    signature = headers['x-hub-signature'] as string;
  }
  if (!signature) {
    logger.error(
      "Github event doesn't have signature. This webhook requires a secret to be configured.",
      LogFields.print(),
    );
    return 500;
  }

  const secret = process.env.WEBHOOK_SECRET || '';
  if (!secret) {
    logger.error('A secret must be configured on the server', LogFields.print());
    return 500;
  }
  const webhooks = new Webhooks({
    secret: secret,
  });
  if (!(await webhooks.verify(body, signature))) {
    logger.error('Unable to verify signature!', LogFields.print());
    return 401;
  }
  return 200;
}

async function handleWorkflowJob(
  body: WorkflowJobEvent,
  githubEvent: string,
): Promise<Response> {
  const installationId = getInstallationId(body);
  if (body.action === 'queued') {
    await sendActionRequest({
      id: body.workflow_job.id,
      repositoryName: body.repository.name,
      repositoryOwner: body.repository.owner.login,
      eventType: githubEvent,
      installationId: installationId,
    });
    logger.info(`Successfully queued job for ${body.repository.full_name}`, LogFields.print());
  }
  return { statusCode: 201 };
}

function getInstallationId(body: WorkflowJobEvent | CheckRunEvent) {
  let installationId = body.installation?.id;
  if (installationId == null) {
    installationId = 0;
  }
  return installationId;
}
