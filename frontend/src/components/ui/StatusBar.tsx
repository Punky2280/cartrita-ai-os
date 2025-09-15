import React from "react";
import { Bot, Zap, Mic, Clock } from "lucide-react";

interface StatusBarProps {
  currentModel: string;
  tokenCount: number;
  voiceActivity: boolean;
  currentTime: Date;
}

const StatusBar: React.FC<StatusBarProps> = ({
  currentModel,
  tokenCount,
  voiceActivity,
  currentTime,
}) => {
  return (
    <div className="h-12 bg-copilot-blue border-t border-gray-600 flex items-center justify-between px-6 text-white text-sm">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4" />
          <span>{currentModel}</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4" />
          <span>{tokenCount} tokens</span>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Mic
            className={`h-4 w-4 ${voiceActivity ? "text-fuschia-pink animate-pulse" : "text-gray-400"}`}
          />
          <span>{voiceActivity ? "Active" : "Inactive"}</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span>{currentTime.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
