import { Webhooks } from '@octokit/webhooks';
import nock from 'nock';

import checkrun_event from '../../test/resources/github_check_run_event.json';
import workflowjob_event from '../../test/resources/github_workflowjob_event.json';
import { sendActionRequest, sendWebhookEventToWorkflowJobQueue } from '../sqs';
import { handle } from './handler';

jest.mock('../sqs');
jest.mock('../ssm');

const GITHUB_APP_WEBHOOK_SECRET = 'TEST_SECRET';

const secret = 'TEST_SECRET';
const webhooks = new Webhooks({
  secret: secret,
});

describe('handler', () => {
  let originalError: Console['error'];

  beforeEach(() => {
    nock.disableNetConnect();
    originalError = console.error;
    console.error = jest.fn();
    jest.clearAllMocks();
    jest.resetAllMocks();
    process.env.WEBHOOK_SECRET = GITHUB_APP_WEBHOOK_SECRET;
  });

  afterEach(() => {
    console.error = originalError;
  });

  it('returns 500 if no signature available', async () => {
    const resp = await handle({}, '');
    expect(resp.statusCode).toBe(500);
  });

  it('returns 401 if signature is invalid', async () => {
    const resp = await handle({ 'X-Hub-Signature': 'bbb' }, 'aaaa');
    expect(resp.statusCode).toBe(401);
  });

  describe('Test for workflowjob event: ', () => {
    it('handles workflow job events', async () => {
      const event = JSON.stringify(workflowjob_event);
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendActionRequest).toBeCalled();
    });

    it('handles workflow job events with 256 hash signature', async () => {
      const event = JSON.stringify(workflowjob_event);
      const resp = await handle(
        { 'X-Hub-Signature-256': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendActionRequest).toBeCalled();
    });

    it('does not handle other events', async () => {
      const event = JSON.stringify(workflowjob_event);
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'push' }, event);
      expect(resp.statusCode).toBe(202);
      expect(sendActionRequest).not.toBeCalled();
    });

    it('does not handle workflow_job events with actions other than queued (action = started)', async () => {
      const event = JSON.stringify({ ...workflowjob_event, action: 'started' });
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendActionRequest).not.toBeCalled();
    });

    it('does not handle workflow_job events with actions other than queued (action = completed)', async () => {
      const event = JSON.stringify({ ...workflowjob_event, action: 'completed' });
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendActionRequest).not.toBeCalled();
    });

    it('handles workflow_job events without installation id', async () => {
      const event = JSON.stringify({ ...workflowjob_event, installation: null });
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendActionRequest).toBeCalled();
    });

    it('returns 500 if signature secret is not available', async () => {
      process.env.WEBHOOK_SECRET = '';
      const event = JSON.stringify(workflowjob_event);
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(500);
    });
  });

  describe('Test for webhook events to be sent to workflow job queue: ', () => {
    beforeEach(() => {
      process.env.SQS_WORKFLOW_JOB_QUEUE =
        'https://sqs.eu-west-1.amazonaws.com/123456789/webhook_events_workflow_job_queue';
    });
    it('sends webhook events to workflow job queue', async () => {
      const event = JSON.stringify(workflowjob_event);
      const resp = await handle(
        { 'X-Hub-Signature': await webhooks.sign(event), 'X-GitHub-Event': 'workflow_job' },
        event,
      );
      expect(resp.statusCode).toBe(201);
      expect(sendWebhookEventToWorkflowJobQueue).toBeCalled();
    });
  });
});
