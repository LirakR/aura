export interface WSMessage<T = Record<string, unknown>> {
  type: string;
  timestamp: string;
  payload: T;
}

export interface ConnectionAckPayload {
  clientId: string;
  serverVersion: string;
}

export interface EngineStatusPayload {
  engine: string;
  status: string;
  version: string;
  fps: number;
}
