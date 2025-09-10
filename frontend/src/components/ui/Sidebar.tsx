import React from 'react';
import { motion } from 'framer-motion';
import { Bot, MessageSquare, Settings, Search, Mic, FileText, BarChart3 } from 'lucide-react';
import { cn } from '@/utils';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  conversations: Array<{ id: string; title?: string; updatedAt: string }>;
  selectedAgent: { id: string; name: string } | null;
  onAgentSelect: (agent: { id: string; name: string }) => void;
  onSettings: () => void;
  onSearch: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  onNewChat,
  conversations,
  selectedAgent,
  onAgentSelect,
  onSettings,
  onSearch
}) => {
  return (
    <motion.div
      initial={{ width: 0 }}
      animate={{ width: isOpen ? 320 : 0 }}
      transition={{ type: 'tween', duration: 0.3 }}
      className={cn(
        "bg-copilot-blue border-r border-gray-600 flex flex-col text-white overflow-hidden",
        "hidden md:flex" // Hide on mobile, show on desktop
      )}
    >
      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-3 h-12 px-4 py-3 bg-cartrita-blue hover:bg-cartrita-blue/80 rounded-lg transition-colors"
        >
          <Bot className="h-5 w-5" />
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 px-4 overflow-y-auto">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Conversations</h3>
        <div className="space-y-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-copilot-blue-light cursor-pointer transition-colors"
            >
              <MessageSquare className="h-4 w-4 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{conv.title || 'Untitled'}</p>
                <p className="text-xs text-gray-400">
                  {new Date(conv.updatedAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Selector */}
      <div className="p-4 border-t border-gray-600">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Agent Selector</h3>
        <div className="space-y-2">
          {/* Agent options would be mapped here */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-copilot-blue-light">
            <Bot className="h-4 w-4" />
            <span className="text-sm">{selectedAgent?.name || 'Cartrita'}</span>
          </div>
        </div>
      </div>

      {/* Voice Controls */}
      <div className="p-4 border-t border-gray-600">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Voice Controls</h3>
        <button className="w-full flex items-center gap-3 h-12 px-4 py-3 bg-fuschia-pink hover:bg-fuschia-pink/80 rounded-lg transition-colors">
          <Mic className="h-5 w-5" />
          Voice Input
        </button>
      </div>

      {/* File Manager */}
      <div className="p-4 border-t border-gray-600">
        <h3 className="text-sm font-medium text-gray-300 mb-3">File Manager</h3>
        <button className="w-full flex items-center gap-3 h-12 px-4 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors">
          <FileText className="h-5 w-5" />
          Upload Files
        </button>
      </div>

      {/* Audio Analytics */}
      <div className="p-4 border-t border-gray-600">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Audio Analytics</h3>
        <button className="w-full flex items-center gap-3 h-12 px-4 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors">
          <BarChart3 className="h-5 w-5" />
          View Analytics
        </button>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-600 flex justify-between">
        <button
          onClick={onSettings}
          className="h-10 w-10 flex items-center justify-center bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors"
        >
          <Settings className="h-5 w-5" />
        </button>
        <button
          onClick={onSearch}
          className="h-10 w-10 flex items-center justify-center bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors"
        >
          <Search className="h-5 w-5" />
        </button>
      </div>
    </motion.div>
  );
};

export default Sidebar;
