import { useWS } from "@/contexts/WebSocketContext";
import { EngineStatusCard } from "./EngineStatusCard";

export function DashboardPage() {
  const { engineStatus } = useWS();

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="aura-fade-in mb-8">
        <h2 className="font-mono text-sm tracking-widest text-muted-foreground uppercase">
          Engine Telemetry
        </h2>
      </div>

      <div
        className="aura-fade-in grid gap-6"
        style={{ animationDelay: "100ms" }}
      >
        <EngineStatusCard engineStatus={engineStatus} />
      </div>

      <div
        className="aura-fade-in mt-12 border-t border-border/30 pt-6"
        style={{ animationDelay: "200ms" }}
      >
        <p className="font-mono text-[11px] tracking-wider text-muted-foreground/50">
          AURA ORCHESTRATOR — VISUAL-CONTEXT-AWARE AI FOR GAME ENGINES
        </p>
      </div>
    </div>
  );
}
