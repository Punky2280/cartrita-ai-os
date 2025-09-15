import React, { useRef, useState } from "react";

interface FileUploaderProps {
  onFiles: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFiles,
  accept,
  multiple,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const arr = Array.from(files);
    onFiles(arr);
    setProgress(100);
    setTimeout(() => setProgress(0), 1000);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${dragActive ? "border-primary bg-muted" : "border-border"}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragActive(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        handleFiles(e.dataTransfer.files);
      }}
      tabIndex={0}
      aria-label="File upload area"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
        tabIndex={-1}
      />
      <button
        type="button"
        className="btn-primary px-4 py-2 rounded"
        onClick={() => inputRef.current?.click()}
        aria-label="Select files to upload"
      >
        Select Files
      </button>
      <div className="mt-2 text-sm text-muted-foreground">
        or drag and drop here
      </div>
      {progress > 0 && (
        <div className="mt-2 w-full bg-muted rounded-full h-2 overflow-hidden">
          <div
            className="bg-primary h-2 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};
