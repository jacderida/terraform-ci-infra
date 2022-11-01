import { Logger } from 'tslog';

export const logger = new Logger({
  colorizePrettyLogs: false,
  displayInstanceName: false,
  minLevel: 'debug',
  name: 'webhook',
  overwriteConsole: true,
  type: 'pretty',
});

export class LogFields {
  static fields: { [key: string]: string } = {};

  public static print(): string {
    return JSON.stringify(LogFields.fields);
  }
}
