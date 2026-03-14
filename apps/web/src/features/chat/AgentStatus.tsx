import { Bot, Loader2, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentTurnState } from "@/types/agent";

interface AgentStatusProps {
  state: AgentTurnState;
}

export function AgentStatus({ state }: AgentStatusProps) {
  if (state === "idle") return null;

  return (
    <div className="flex items-center gap-2 px-4 py-1.5 border-t border-border/30">
      {state === "thinking" && (
        <>
          <Loader2 className="size-3.5 animate-spin text-aura-cyan" />
          <span className="font-mono text-xs text-muted-foreground aura-pulse">
            Agent is thinking...
          </span>
        </>
      )}
      {state === "awaiting_approval" && (
        <>
          <ShieldAlert className="size-3.5 text-aura-amber" />
          <span className="font-mono text-xs text-aura-amber">
            Awaiting approval
          </span>
        </>
      )}
    </div>
  );
}
