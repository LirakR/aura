import { useCallback, useEffect, useReducer } from "react";
import { useWS } from "@/contexts/WebSocketContext";
import type { AgentTurnState, ApprovalRequest, TurnItem } from "@/types/agent";

// ── State ──────────────────────────────────────────────────────────

interface AgentState {
  turnState: AgentTurnState;
  streamingText: string;
  streamingItemId: string | null;
  items: TurnItem[];
  approvalRequest: ApprovalRequest | null;
}

const initialState: AgentState = {
  turnState: "idle",
  streamingText: "",
  streamingItemId: null,
  items: [],
  approvalRequest: null,
};

// ── Actions ────────────────────────────────────────────────────────

type Action =
  | { type: "TURN_STARTED" }
  | { type: "TURN_COMPLETED" }
  | { type: "ITEM_STARTED"; item_id: string; item_type: string }
  | { type: "ITEM_COMPLETED"; item_id: string; item_type: string; text?: string; data?: Record<string, unknown> }
  | { type: "MESSAGE_DELTA"; item_id: string; delta: string }
  | { type: "ITEM_OUTPUT"; item_id: string; delta: string }
  | { type: "APPROVAL_REQUEST"; request: ApprovalRequest }
  | { type: "APPROVAL_RESPONDED" }
  | { type: "ERROR" };

function reducer(state: AgentState, action: Action): AgentState {
  switch (action.type) {
    case "TURN_STARTED":
      return {
        ...initialState,
        turnState: "thinking",
      };

    case "TURN_COMPLETED":
      return {
        ...state,
        turnState: "idle",
        streamingText: "",
        streamingItemId: null,
        approvalRequest: null,
      };

    case "ITEM_STARTED": {
      const item: TurnItem = {
        id: action.item_id,
        type: action.item_type as TurnItem["type"],
        status: "running",
      };
      const newState: AgentState = {
        ...state,
        items: [...state.items, item],
      };
      if (action.item_type === "message") {
        // New message item — reset streaming buffer
        newState.streamingText = "";
        newState.streamingItemId = action.item_id;
      }
      return newState;
    }

    case "ITEM_COMPLETED": {
      const items = state.items.map((it) =>
        it.id === action.item_id
          ? {
              ...it,
              status: "completed" as const,
              text: action.text ?? it.text,
              ...(action.data ? action.data : {}),
            }
          : it,
      );
      return {
        ...state,
        items,
        // If this was the streaming message, clear it
        streamingText:
          state.streamingItemId === action.item_id ? "" : state.streamingText,
        streamingItemId:
          state.streamingItemId === action.item_id ? null : state.streamingItemId,
      };
    }

    case "MESSAGE_DELTA":
      // Only accumulate if this delta belongs to the current streaming item
      if (action.item_id !== state.streamingItemId) return state;
      return {
        ...state,
        streamingText: state.streamingText + action.delta,
      };

    case "ITEM_OUTPUT": {
      const items = state.items.map((it) =>
        it.id === action.item_id
          ? { ...it, output: (it.output ?? "") + action.delta }
          : it,
      );
      return { ...state, items };
    }

    case "APPROVAL_REQUEST":
      return {
        ...state,
        turnState: "awaiting_approval",
        approvalRequest: action.request,
      };

    case "APPROVAL_RESPONDED":
      return {
        ...state,
        turnState: "thinking",
        approvalRequest: null,
      };

    case "ERROR":
      return {
        ...state,
        turnState: "idle",
        streamingText: "",
        streamingItemId: null,
      };

    default:
      return state;
  }
}

// ── Hook ───────────────────────────────────────────────────────────

export function useAgent(threadId: string | null) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { subscribe, send } = useWS();

  useEffect(() => {
    if (!threadId) return;

    const tid = threadId;

    // Use stable keys so re-subscriptions replace, never duplicate
    const key = `agent-${tid}`;

    const unsubs = [
      subscribe("agent.turn.started", (msg) => {
        if ((msg.payload as any).thread_id === tid)
          dispatch({ type: "TURN_STARTED" });
      }, `${key}-ts`),

      subscribe("agent.turn.completed", (msg) => {
        if ((msg.payload as any).thread_id === tid)
          dispatch({ type: "TURN_COMPLETED" });
      }, `${key}-tc`),

      subscribe("agent.item.started", (msg) => {
        const p = msg.payload as any;
        if (p.thread_id === tid)
          dispatch({
            type: "ITEM_STARTED",
            item_id: p.item_id,
            item_type: p.item_type,
          });
      }, `${key}-is`),

      subscribe("agent.item.completed", (msg) => {
        const p = msg.payload as any;
        if (p.thread_id === tid)
          dispatch({
            type: "ITEM_COMPLETED",
            item_id: p.item_id,
            item_type: p.item_type,
            text: p.text ?? undefined,
            data: p.data ?? undefined,
          });
      }, `${key}-ic`),

      subscribe("agent.message.delta", (msg) => {
        const p = msg.payload as any;
        if (p.thread_id === tid)
          dispatch({
            type: "MESSAGE_DELTA",
            item_id: p.item_id,
            delta: p.delta,
          });
      }, `${key}-md`),

      subscribe("agent.item.output", (msg) => {
        const p = msg.payload as any;
        if (p.thread_id === tid)
          dispatch({
            type: "ITEM_OUTPUT",
            item_id: p.item_id,
            delta: p.delta,
          });
      }, `${key}-io`),

      subscribe("agent.approval.request", (msg) => {
        const p = msg.payload as any;
        if (p.thread_id === tid && p.request_id && p.data)
          dispatch({
            type: "APPROVAL_REQUEST",
            request: {
              request_id: p.request_id,
              thread_id: p.thread_id,
              tool_name: p.data.tool_name,
              tool_args: p.data.tool_args,
              description: p.data.description,
            },
          });
      }, `${key}-ar`),

      subscribe("agent.error", (msg) => {
        if ((msg.payload as any).thread_id === tid)
          dispatch({ type: "ERROR" });
      }, `${key}-err`),
    ];

    return () => {
      for (const unsub of unsubs) unsub();
    };
  }, [threadId, subscribe]);

  const sendToAgent = useCallback(
    (tid: string, content: string) => {
      send({
        type: "chat.send",
        timestamp: new Date().toISOString(),
        payload: { thread_id: tid, content },
      });
    },
    [send],
  );

  const interrupt = useCallback(
    (tid: string) => {
      send({
        type: "agent.interrupt",
        timestamp: new Date().toISOString(),
        payload: { thread_id: tid },
      });
    },
    [send],
  );

  const respondToApproval = useCallback(
    (tid: string, requestId: string, decision: "approve" | "deny") => {
      send({
        type: "agent.approval.respond",
        timestamp: new Date().toISOString(),
        payload: { thread_id: tid, request_id: requestId, decision },
      });
      dispatch({ type: "APPROVAL_RESPONDED" });
    },
    [send],
  );

  return {
    ...state,
    sendToAgent,
    interrupt,
    respondToApproval,
  };
}
