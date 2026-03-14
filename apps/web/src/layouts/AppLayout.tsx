import { NavLink, Outlet } from "react-router";
import { Activity, MessageSquare, Gauge, Wifi, WifiOff, Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useWS, type ConnectionStatus } from "@/contexts/WebSocketContext";
import { cn } from "@/lib/utils";

const statusConfig: Record<
  ConnectionStatus,
  {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
    iconClass: string;
    dotClass: string;
  }
> = {
  connected: {
    label: "Connected",
    variant: "outline",
    iconClass: "text-aura-green",
    dotClass: "bg-aura-green",
  },
  connecting: {
    label: "Connecting\u2026",
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

const navItems = [
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
];

export function AppLayout() {
  const { status, serverVersion } = useWS();
  const config = statusConfig[status];
  const StatusIcon =
    status === "connected" ? Wifi : status === "connecting" ? Radio : WifiOff;

  return (
    <div className="aura-noise aura-grid-bg relative flex min-h-screen flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-10 border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Activity className="size-5 text-aura-cyan" />
              <h1 className="font-mono text-lg font-bold tracking-tight">
                AURA
              </h1>
              {serverVersion && (
                <span className="font-mono text-xs text-muted-foreground">
                  v{serverVersion}
                </span>
              )}
            </div>

            <nav className="flex items-center gap-1 ml-4">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-1.5 rounded-md px-3 py-1.5 font-mono text-xs transition-colors",
                      isActive
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                    )
                  }
                >
                  <Icon className="size-3.5" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <StatusIcon className={cn("size-4", config.iconClass)} />
            <ConnectionBadge status={status} />
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="relative z-[1] flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
