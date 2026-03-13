import { Activity, Wifi, WifiOff, Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useWebSocket, type ConnectionStatus } from "@/hooks/use-websocket";
import { EngineStatusCard } from "./EngineStatusCard";
import { cn } from "@/lib/utils";

const WS_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`;

const statusConfig: Record<
  ConnectionStatus,
  { label: string; variant: "default" | "secondary" | "outline" | "destructive"; iconClass: string; dotClass: string }
> = {
  connected: {
    label: "Connected",
    variant: "outline",
    iconClass: "text-aura-green",
    dotClass: "bg-aura-green",
  },
  connecting: {
    label: "Connecting…",
    variant: "secondary",
    iconClass: "text-aura-amber",
    dotClass: "bg-aura-amber aura-pulse",
  },
  disconnected: {
    label: "Disconnected",
    variant: "destructive",
    iconClass: "text-muted-foreground/40",
    dotClass: "bg-aura-red",
  },
};

function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="gap-2 font-mono text-xs">
      <span className={cn("size-1.5 rounded-full", config.dotClass)} />
      {config.label}
    </Badge>
  );
}

export function Dashboard() {
  const { status, serverVersion, engineStatus } = useWebSocket(WS_URL);

  const config = statusConfig[status];
  const StatusIcon =
    status === "connected" ? Wifi : status === "connecting" ? Radio : WifiOff;

  return (
    <div className="aura-noise aura-grid-bg relative min-h-screen">
      {/* Top bar */}
      <header className="aura-fade-in sticky top-0 z-10 border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Activity className="text-aura-cyan" />
            <h1 className="font-mono text-lg font-bold tracking-tight">
              AURA
            </h1>
            {serverVersion && (
              <span className="font-mono text-xs text-muted-foreground">
                v{serverVersion}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <StatusIcon className={cn("size-4", config.iconClass)} />
            <ConnectionBadge status={status} />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-[1] mx-auto max-w-5xl px-6 py-10">
        <div
          className="aura-fade-in mb-8"
          style={{ animationDelay: "100ms" }}
        >
          <h2 className="font-mono text-sm tracking-widest text-muted-foreground uppercase">
            Engine Telemetry
          </h2>
        </div>

        <div
          className="aura-fade-in grid gap-6"
          style={{ animationDelay: "200ms" }}
        >
          <EngineStatusCard engineStatus={engineStatus} />
        </div>

        {/* Footer info */}
        <div
          className="aura-fade-in mt-12 border-t border-border/30 pt-6"
          style={{ animationDelay: "300ms" }}
        >
          <p className="font-mono text-[11px] tracking-wider text-muted-foreground/50">
            AURA ORCHESTRATOR — VISUAL-CONTEXT-AWARE AI FOR GAME ENGINES
          </p>
        </div>
      </main>
    </div>
  );
}
