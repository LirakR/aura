export type MessageRole = "user" | "assistant" | "system";

export interface ChatThread {
  id: string;
  project: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  thread: string;
  role: MessageRole;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface PaginatedMessages {
  messages: ChatMessage[];
  cursor: string | null;
  has_more: boolean;
}
