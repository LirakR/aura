import { Cpu, Gauge } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardAction,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { EngineStatusPayload } from "@/types/websocket";
import { cn } from "@/lib/utils";

interface EngineStatusCardProps {
  engineStatus: EngineStatusPayload | null;
}

function FpsReadout({ fps }: { fps: number | null }) {
  const value = fps !== null ? fps.toFixed(1) : "—";
  const isGood = fps !== null && fps >= 55;
  const isWarn = fps !== null && fps >= 30 && fps < 55;

  return (
    <div className="flex items-baseline gap-2">
      <span
        className={cn(
          "font-mono text-5xl font-bold tracking-tighter tabular-nums transition-colors duration-300",
          fps === null && "text-muted-foreground/30",
          isGood && "text-aura-green",
          isWarn && "text-aura-amber",
          fps !== null && fps < 30 && "text-aura-red"
        )}
      >
        {value}
      </span>
      <span className="font-mono text-sm tracking-wider text-muted-foreground uppercase">
        fps
      </span>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const isRunning = status === "running";
  return (
    <span className="relative flex size-2">
      {isRunning && (
        <span className="absolute inline-flex size-full animate-ping rounded-full bg-aura-green opacity-75" />
      )}
      <span
        className={cn(
          "relative inline-flex size-2 rounded-full",
          isRunning ? "bg-aura-green" : "bg-muted-foreground/40"
        )}
      />
    </span>
  );
}

export function EngineStatusCard({ engineStatus }: EngineStatusCardProps) {
  const hasData = engineStatus !== null;

  return (
    <Card className="aura-fade-in relative overflow-hidden">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Cpu className="text-aura-cyan" data-icon />
          <CardTitle>
            {hasData
              ? `${engineStatus.engine} ${engineStatus.version}`
              : "No Engine"}
          </CardTitle>
        </div>
        <CardDescription>
          {hasData ? "Connected game engine instance" : "Waiting for engine data…"}
        </CardDescription>
        <CardAction>
          {hasData && (
            <div className="flex items-center gap-2">
              <StatusDot status={engineStatus.status} />
              <Badge variant="outline" className="font-mono text-xs uppercase">
                {engineStatus.status}
              </Badge>
            </div>
          )}
        </CardAction>
      </CardHeader>

      <CardContent>
        <div className="flex items-center gap-3">
          <Gauge className="text-muted-foreground" data-icon />
          <FpsReadout fps={hasData ? engineStatus.fps : null} />
        </div>

        {hasData && (
          <div className="mt-4 flex gap-6 border-t border-border/50 pt-4">
            <Stat label="Engine" value={engineStatus.engine} />
            <Stat label="Version" value={`v${engineStatus.version}`} />
            <Stat label="Protocol" value="WebSocket" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[10px] tracking-widest text-muted-foreground uppercase">
        {label}
      </span>
      <span className="font-mono text-sm text-foreground">{value}</span>
    </div>
  );
}
