/**
 * EnhancedMessageInput Component - Cartrita AI OS v2
 *
 * Modern chat input with auto-resize, attachments, agent selection
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import {
  SendIcon,
  PaperclipIcon,
  MicIcon,
  StopCircleIcon,
  ChevronDownIcon,
  XIcon
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: 'coding' | 'research' | 'creative' | 'analysis';
  avatar?: string;
  color: string;
}

interface Attachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'code';
  size?: number;
  url?: string;
}

interface EnhancedMessageInputProps {
  className?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: (message: string, attachments: Attachment[], selectedAgent?: Agent) => void;
  disabled?: boolean;
  isLoading?: boolean;
  agents?: Agent[];
  selectedAgent?: Agent;
  onAgentSelect?: (agent: Agent) => void;
  maxLength?: number;
  allowAttachments?: boolean;
  allowVoiceInput?: boolean;
  attachments?: Attachment[];
  onAttachmentAdd?: (attachment: Attachment) => void;
  onAttachmentRemove?: (attachmentId: string) => void;
}

export function EnhancedMessageInput({
  className,
  placeholder = "Message Cartrita AI...",
  value,
  onChange,
  onSubmit,
  disabled = false,
  isLoading = false,
  agents = [],
  selectedAgent,
  onAgentSelect,
  maxLength = 4000,
  allowAttachments = true,
  allowVoiceInput = true,
  attachments = [],
  onAttachmentAdd,
  onAttachmentRemove
}: EnhancedMessageInputProps) {
  const [inputValue, setInputValue] = useState(value || '');
  const [isRecording, setIsRecording] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, []);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    if (newValue.length <= maxLength) {
      setInputValue(newValue);
      onChange?.(newValue);
      adjustTextareaHeight();
    }
  };

  // Handle submit
  const handleSubmit = () => {
    if (inputValue.trim() && !disabled && !isLoading) {
      onSubmit?.(inputValue.trim(), attachments, selectedAgent);
      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => {
      const attachment: Attachment = {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        type: file.type.startsWith('image/') ? 'image' : 'file',
        size: file.size,
        url: URL.createObjectURL(file)
      };
      onAttachmentAdd?.(attachment);
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Voice recording toggle
  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording logic
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [adjustTextareaHeight]);

  useEffect(() => {
    if (value !== undefined) {
      setInputValue(value);
    }
  }, [value]);

  const hasContent = inputValue.trim().length > 0 || attachments.length > 0;

  return (
    <div className={cn(
      'relative bg-gray-900 border border-gray-700 rounded-xl p-4 focus-within:border-copilot-blue/50 transition-colors',
      className
    )}>
      {/* Agent Selector */}
      {agents.length > 0 && (
        <div className="mb-3 relative">
          <button
            type="button"
            onClick={() => setShowAgentSelector(!showAgentSelector)}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg hover:bg-gray-700 transition-colors text-sm"
          >
            {selectedAgent ? (
              <>
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: selectedAgent.color }}
                />
                <span className="text-gray-200">{selectedAgent.name}</span>
              </>
            ) : (
              <span className="text-gray-400">Select Agent</span>
            )}
            <ChevronDownIcon className="w-4 h-4 text-gray-400" />
          </button>

          {/* Agent Dropdown */}
          {showAgentSelector && (
            <div className="absolute top-full left-0 mt-2 w-64 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50">
              <div className="p-2">
                {agents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => {
                      onAgentSelect?.(agent);
                      setShowAgentSelector(false);
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-700 transition-colors text-left"
                  >
                    <div
                      className="w-6 h-6 rounded-full flex-shrink-0"
                      style={{ backgroundColor: agent.color }}
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-200">
                        {agent.name}
                      </div>
                      <div className="text-xs text-gray-400 capitalize">
                        {agent.type}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map(attachment => (
            <div
              key={attachment.id}
              className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-sm"
            >
              <PaperclipIcon className="w-4 h-4 text-gray-400" />
              <span className="text-gray-200 truncate max-w-32">
                {attachment.name}
              </span>
              <button
                onClick={() => onAttachmentRemove?.(attachment.id)}
                className="text-gray-400 hover:text-red-400 transition-colors"
              >
                <XIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-3">
        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'w-full bg-transparent text-gray-100 placeholder-gray-400',
              'resize-none outline-none min-h-[24px] max-h-[200px]',
              'scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-600'
            )}
            rows={1}
          />

          {/* Character Count */}
          {maxLength && inputValue.length > maxLength * 0.8 && (
            <div className={cn(
              'absolute bottom-0 right-0 text-xs px-2 py-1 rounded-tl-md',
              inputValue.length >= maxLength
                ? 'text-red-400 bg-red-400/10'
                : 'text-yellow-400 bg-yellow-400/10'
            )}>
              {inputValue.length}/{maxLength}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Attachment Button */}
          {allowAttachments && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileUpload}
                className="hidden"
                accept="image/*,.pdf,.doc,.docx,.txt,.json,.xml,.csv"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PaperclipIcon className="w-5 h-5" />
              </button>
            </>
          )}

          {/* Voice Input Button */}
          {allowVoiceInput && (
            <button
              type="button"
              onClick={toggleRecording}
              disabled={disabled}
              className={cn(
                'p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
                isRecording
                  ? 'text-red-400 bg-red-400/10 hover:bg-red-400/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
              )}
            >
              {isRecording ? (
                <StopCircleIcon className="w-5 h-5" />
              ) : (
                <MicIcon className="w-5 h-5" />
              )}
            </button>
          )}

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || !hasContent || isLoading}
            className={cn(
              'p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
              hasContent && !disabled && !isLoading
                ? 'text-white bg-copilot-blue hover:bg-copilot-blue/80'
                : 'text-gray-400 bg-gray-700 hover:bg-gray-600'
            )}
          >
            <SendIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Close Agent Selector on Outside Click */}
      {showAgentSelector && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowAgentSelector(false)}
        />
      )}
    </div>
  );
}

export default EnhancedMessageInput;
