export type AgentTurnState = "idle" | "thinking" | "awaiting_approval";

export type TurnItemType = "message" | "command" | "file_change" | "reasoning";

export interface TurnItem {
  id: string;
  type: TurnItemType;
  status: "running" | "completed";
  text?: string;
  command?: string;
  cwd?: string;
  output?: string;
  files?: string[];
}

export interface ApprovalRequest {
  request_id: string;
  thread_id: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  description: string;
}
