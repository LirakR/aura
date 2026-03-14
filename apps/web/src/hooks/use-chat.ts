import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useWS } from "@/contexts/WebSocketContext";
import type {
  ChatThread,
  ChatMessage,
  PaginatedMessages,
} from "@/types/chat";

// ── Threads ────────────────────────────────────────────────────────

export function useThreads(project: string | null) {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!project) {
      setThreads([]);
      return;
    }
    setLoading(true);
    try {
      const data = await api.get<ChatThread[]>(
        `/chat/threads?project=${encodeURIComponent(project)}`,
      );
      setThreads(data);
    } catch (err) {
      console.error("Failed to load threads", err);
    } finally {
      setLoading(false);
    }
  }, [project]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { threads, loading, refresh };
}

// ── Messages ───────────────────────────────────────────────────────

export function useMessages(threadId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const cursorRef = useRef<string | null>(null);
  const { subscribe } = useWS();

  const load = useCallback(async () => {
    if (!threadId) {
      setMessages([]);
      return;
    }
    setLoading(true);
    try {
      const data = await api.get<PaginatedMessages>(
        `/chat/threads/${threadId}/messages`,
      );
      setMessages(data.messages);
      cursorRef.current = data.cursor;
      setHasMore(data.has_more);
    } catch (err) {
      console.error("Failed to load messages", err);
    } finally {
      setLoading(false);
    }
  }, [threadId]);

  const loadMore = useCallback(async () => {
    if (!threadId || !cursorRef.current) return;
    try {
      const data = await api.get<PaginatedMessages>(
        `/chat/threads/${threadId}/messages?cursor=${encodeURIComponent(cursorRef.current)}`,
      );
      setMessages((prev) => [...data.messages, ...prev]);
      cursorRef.current = data.cursor;
      setHasMore(data.has_more);
    } catch (err) {
      console.error("Failed to load more messages", err);
    }
  }, [threadId]);

  // Initial load
  useEffect(() => {
    load();
  }, [load]);

  // Live updates via WS
  useEffect(() => {
    if (!threadId) return;
    const unsub = subscribe("chat.message.new", (msg) => {
      const payload = msg.payload as { thread_id: string; message: ChatMessage };
      if (payload.thread_id === threadId) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === payload.message.id)) return prev;
          return [...prev, payload.message];
        });
      }
    }, `chat-msg-${threadId}`);
    return unsub;
  }, [threadId, subscribe]);

  return { messages, loading, hasMore, loadMore, refresh: load };
}

// ── Send ───────────────────────────────────────────────────────────

export function useSendMessage() {
  const [sending, setSending] = useState(false);

  const sendMessage = useCallback(
    async (threadId: string, content: string) => {
      setSending(true);
      try {
        await api.post(`/chat/threads/${threadId}/messages`, {
          role: "user",
          content,
        });
      } catch (err) {
        console.error("Failed to send message", err);
        throw err;
      } finally {
        setSending(false);
      }
    },
    [],
  );

  return { sendMessage, sending };
}
