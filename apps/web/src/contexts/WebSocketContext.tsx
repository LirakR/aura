import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type {
  WSMessage,
  ConnectionAckPayload,
  EngineStatusPayload,
} from "@/types/websocket";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

type Callback = (msg: WSMessage) => void;

interface WebSocketContextValue {
  status: ConnectionStatus;
  clientId: string | null;
  serverVersion: string | null;
  engineStatus: EngineStatusPayload | null;
  subscribe: (type: string, cb: Callback, key?: string) => () => void;
  send: (msg: WSMessage) => void;
}

const Ctx = createContext<WebSocketContextValue | null>(null);

const WS_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`;

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [clientId, setClientId] = useState<string | null>(null);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [engineStatus, setEngineStatus] = useState<EngineStatusPayload | null>(
    null,
  );

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);
  const pingInterval = useRef<ReturnType<typeof setInterval>>(undefined);
  // Keyed map: type -> key -> callback. Only one cb per key per type.
  const subsRef = useRef<Map<string, Map<string, Callback>>>(new Map());
  const keyCounterRef = useRef(0);

  const subscribe = useCallback((type: string, cb: Callback, key?: string) => {
    const subs = subsRef.current;
    if (!subs.has(type)) subs.set(type, new Map());
    const k = key ?? `_auto_${++keyCounterRef.current}`;
    subs.get(type)!.set(k, cb);
    return () => {
      subs.get(type)?.delete(k);
    };
  }, []);

  const send = useCallback((msg: WSMessage) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      pingInterval.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "heartbeat.ping",
              timestamp: new Date().toISOString(),
              payload: {},
            }),
          );
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      // Built-in handling
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

      // Route to subscribers
      const cbs = subsRef.current.get(msg.type);
      if (cbs) {
        for (const cb of cbs.values()) cb(msg);
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
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      clearInterval(pingInterval.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return (
    <Ctx.Provider
      value={{
        status,
        clientId,
        serverVersion,
        engineStatus,
        subscribe,
        send,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useWS(): WebSocketContextValue {
  const ctx = useContext(Ctx);
  if (!ctx)
    throw new Error("useWS must be used within a WebSocketProvider");
  return ctx;
}
