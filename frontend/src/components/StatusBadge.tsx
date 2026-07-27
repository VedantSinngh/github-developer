import React from "react";

interface StatusBadgeProps {
  status: "pending" | "active" | "completed" | "locked" | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const styles: Record<string, string> = {
    pending: "bg-surface-strong text-muted border-hairline",
    active: "bg-surface-strong text-ink font-medium border-hairline-strong animate-pulse",
    completed: "bg-surface-strong text-body-strong border-hairline",
    locked: "bg-ink text-surface-card border-ink font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-pill text-caption-uppercase border transition-colors ${
        styles[status] || "bg-surface-strong text-body border-hairline"
      }`}
    >
      {status === "locked" && <span className="mr-1.5 text-[10px]">🔒</span>}
      {status === "active" && <span className="w-1.5 h-1.5 rounded-full bg-ink mr-1.5 animate-pulse"></span>}
      {status}
    </span>
  );
};
