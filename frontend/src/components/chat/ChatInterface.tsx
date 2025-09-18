import { Paperclip, Mic, Send, Bot } from "lucide-react";

export function ChatInterface() {
  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <div className="flex-1 space-y-6 overflow-y-auto p-4">
        {/* Placeholder for messages */}
        <div className="text-center text-gpt-gray-400 py-20">
          <Bot size={48} className="mx-auto text-gpt-gray-500" />
          <h3 className="mt-4 text-lg font-medium">Your conversation with Cartrita starts here.</h3>
          <p className="text-sm text-gpt-gray-500">Ask a question, upload a file, or give a command.</p>
        </div>
      </div>
      <div className="p-4 bg-gpt-gray-900/50 sticky bottom-0">
        <div className="relative">
          <textarea
            className="w-full bg-gpt-gray-800 rounded-lg p-4 pr-32 text-gpt-gray-100 focus:outline-none focus:ring-2 focus:ring-copilot-blue border border-gpt-gray-700"
            placeholder="Ask Cartrita anything..."
            rows={1}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-2">
            <button className="p-2 rounded-md hover:bg-gpt-gray-700">
              <Paperclip className="w-5 h-5 text-gpt-gray-400" />
            </button>
            <button className="p-2 rounded-md hover:bg-gpt-gray-700">
              <Mic className="w-5 h-5 text-gpt-gray-400" />
            </button>
            <button className="p-2 rounded-md bg-copilot-blue hover:bg-opacity-80">
              <Send className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
