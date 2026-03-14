import { ShieldAlert, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ApprovalRequest } from "@/types/agent";

interface ApprovalCardProps {
  request: ApprovalRequest;
  onRespond: (decision: "approve" | "deny") => void;
}

export function ApprovalCard({ request, onRespond }: ApprovalCardProps) {
  return (
    <div className="flex justify-start py-1.5">
      <Card className="max-w-[80%] border-aura-amber/30 bg-aura-amber/5">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <ShieldAlert className="size-5 shrink-0 text-aura-amber mt-0.5" />
            <div className="flex-1 space-y-2">
              <p className="font-mono text-xs font-medium text-foreground">
                Approval Required
              </p>
              <p className="font-mono text-xs text-muted-foreground">
                {request.description || `${request.tool_name}`}
              </p>
              {Object.keys(request.tool_args).length > 0 && (
                <pre className="rounded-md bg-background/50 p-2 font-mono text-[11px] text-muted-foreground overflow-x-auto">
                  {JSON.stringify(request.tool_args, null, 2)}
                </pre>
              )}
              <div className="flex gap-2 pt-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 font-mono text-xs text-aura-green border-aura-green/30 hover:bg-aura-green/10"
                  onClick={() => onRespond("approve")}
                >
                  <Check className="size-3" />
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 font-mono text-xs text-aura-red border-aura-red/30 hover:bg-aura-red/10"
                  onClick={() => onRespond("deny")}
                >
                  <X className="size-3" />
                  Deny
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
