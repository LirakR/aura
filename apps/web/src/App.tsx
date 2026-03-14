import { RouterProvider } from "react-router";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { ChatProvider } from "@/contexts/ChatContext";
import { TooltipProvider } from "@/components/ui/tooltip";
import { router } from "@/router";

export default function App() {
  return (
    <WebSocketProvider>
      <ChatProvider>
        <TooltipProvider>
          <RouterProvider router={router} />
        </TooltipProvider>
      </ChatProvider>
    </WebSocketProvider>
  );
}
