import { useCallback, useEffect, useRef, useState } from "react";
import type {
  WSMessage,
  ConnectionAckPayload,
  EngineStatusPayload,
} from "@/types/websocket";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface UseWebSocketReturn {
  status: ConnectionStatus;
  clientId: string | null;
  serverVersion: string | null;
  engineStatus: EngineStatusPayload | null;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [clientId, setClientId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [engineStatus, setEngineStatus] = useState<EngineStatusPayload | null>(
    null
  );

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);
  const pingInterval = useRef<ReturnType<typeof setInterval>>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      pingInterval.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({ type: "heartbeat.ping", timestamp: new Date().toISOString(), payload: {} })
          );
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      switch (msg.type) {
        case "connection.ack": {
          const payload = msg.payload as unknown as ConnectionAckPayload;
          setClientId(payload.clientId);
          setServerVersion(payload.serverVersion);
          break;
        }
        case "engine.status": {
          const payload = msg.payload as unknown as EngineStatusPayload;
          setEngineStatus(payload);
          break;
        }
        case "engine.disconnect": {
          setEngineStatus(null);
          break;
        }
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      setEngineStatus(null);
      clearInterval(pingInterval.current);
      wsRef.current = null;
      reconnectTimeout.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      clearInterval(pingInterval.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, clientId, serverVersion, engineStatus };
}
