import React from "react";

export type AgentTaskEvent = {
  id: string;
  status: "started" | "progress" | "completed";
  progress?: number;
  label?: string;
  startedAt?: string;
  updatedAt?: string;
};

type Props = {
  events: AgentTaskEvent[];
};

export function AgentTaskTimeline({ events }: Props) {
  if (!events.length) return null;

  return (
    <div className="mt-3 rounded-md border border-neutral-200 dark:border-neutral-800 p-3">
      <div className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-2">
        Agent tasks
      </div>
      <ul className="space-y-2">
        {events.map((evt) => (
          <li key={evt.id} className="flex items-center gap-3 text-sm">
            <span
              className={
                evt.status === "completed"
                  ? "inline-block h-2 w-2 rounded-full bg-emerald-500"
                  : evt.status === "progress"
                    ? "inline-block h-2 w-2 rounded-full bg-amber-500"
                    : "inline-block h-2 w-2 rounded-full bg-sky-500"
              }
            />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-neutral-800 dark:text-neutral-200">
                  {evt.label || evt.id}
                </span>
                <span className="text-xs text-neutral-500 dark:text-neutral-400">
                  {evt.status}
                </span>
              </div>
              {typeof evt.progress === "number" && (
                <div className="mt-1 h-1.5 w-full rounded bg-neutral-100 dark:bg-neutral-900">
                  <div
                    className="h-1.5 rounded bg-amber-500"
                    style={{
                      width: `${Math.max(0, Math.min(100, evt.progress))}%`,
                    }}
                  />
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AgentTaskTimeline;
