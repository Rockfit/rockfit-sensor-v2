import { MqttClient, IClientOptions } from 'mqtt';

export interface Error {
  name: string;
  message: string;
  stack?: string;
}

export interface ConnectorProps {
  brokerUrl: string;
  options?: IClientOptions;
  parserMethod?: (message) => string;
  children: React.ReactNode;
}

export interface IMqttContext {
  connectionStatus: string | Error;
  client?: MqttClient | null;
  parserMethod?: (message: any) => string;
}

export interface IMessageStructure {
  [key: string]: string;
}

export interface IMessage {
  topic: string;
  id: number;
  message?: string | IMessageStructure;
}

export interface IUseSubscription {
  topic: string | string[];
  client?: MqttClient | null;
  message?: IMessage;
  messages?: IMessage[];
  setMessages?: (messages: IMessage[]) => void;
  clearMessages: () => void;
  connectionStatus: string | Error;
}

export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;