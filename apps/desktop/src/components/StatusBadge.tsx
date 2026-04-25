type StatusBadgeProps = {
  status: "ready" | "mock" | "warning" | "queued" | "running" | "done" | "blocked";
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status status-${status}`}>{status}</span>;
}
