import React from "react";

export type AttachmentItem = {
  id: string;
  name: string;
  size: number;
  type: string;
  progress?: number; // 0..100 if uploading
  previewUrl?: string;
  error?: string;
};

type Props = {
  items: AttachmentItem[];
  onRemove?: (id: string) => void;
  onOpen?: (id: string) => void;
};

export default function AttachmentsBar({ items, onRemove, onOpen }: Props) {
  if (!items?.length) return null;
  return (
    <div className="w-full border-t border-gray-800 bg-gray-950/80 p-2">
      <ul className="flex gap-2 overflow-x-auto" aria-label="Attachments">
        {items.map((a) => (
          <li
            key={a.id}
            className="min-w-[180px] max-w-[220px] border border-gray-800 rounded p-2 bg-gray-900"
          >
            <div className="flex items-center justify-between gap-2">
              <button
                onClick={() => onOpen?.(a.id)}
                className="truncate text-left text-sm hover:underline"
                title={`${a.name} (${formatSize(a.size)})`}
              >
                {a.name}
              </button>
              {onRemove && (
                <button
                  onClick={() => onRemove(a.id)}
                  aria-label={`Remove ${a.name}`}
                  className="text-xs rounded bg-gray-800 hover:bg-gray-700 px-2 py-0.5"
                >
                  Remove
                </button>
              )}
            </div>
            {a.progress !== undefined && (
              <div className="mt-2 h-1.5 bg-gray-800 rounded">
                <div
                  className="h-full bg-emerald-600 rounded"
                  style={{
                    width: `${Math.max(0, Math.min(100, a.progress))}%`,
                  }}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={a.progress}
                  role="progressbar"
                />
              </div>
            )}
            {a.error && (
              <div className="mt-2 text-xs text-red-400" role="status">
                {a.error}
              </div>
            )}
            {a.previewUrl && (
              <div className="mt-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={a.previewUrl}
                  alt="Attachment preview"
                  className="w-full h-24 object-cover rounded border border-gray-800"
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function formatSize(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  return `${(n / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}
