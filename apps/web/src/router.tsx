import { createBrowserRouter, Navigate } from "react-router";
import { AppLayout } from "@/layouts/AppLayout";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      {
        path: "chat",
        lazy: () =>
          import("@/features/chat/ChatPage").then((m) => ({
            Component: m.ChatPage,
          })),
      },
      {
        path: "chat/:threadId",
        lazy: () =>
          import("@/features/chat/ChatPage").then((m) => ({
            Component: m.ChatPage,
          })),
      },
      {
        path: "dashboard",
        lazy: () =>
          import("@/features/dashboard/DashboardPage").then((m) => ({
            Component: m.DashboardPage,
          })),
      },
    ],
  },
]);
