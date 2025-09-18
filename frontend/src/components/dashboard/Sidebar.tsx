import { Bot, Code, Settings, Workflow, KeyRound, BrainCircuit } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-64 bg-gpt-gray-900/50 backdrop-blur-sm p-6 flex-col border-r border-gpt-gray-700 hidden md:flex">
      <h1 className="text-2xl font-bold text-skittles mb-10">Dat Bitch Cartrita</h1>
      <nav className="space-y-2 flex-1">
        <a href="#" className="flex items-center p-3 text-gpt-gray-100 rounded-lg bg-gpt-gray-700/50">
          <Bot className="w-5 h-5 mr-3 text-copilot-blue" />
          Chat
        </a>
        <a href="#" className="flex items-center p-3 text-gpt-gray-300 rounded-lg hover:bg-gpt-gray-700/50">
          <Workflow className="w-5 h-5 mr-3 text-copilot-pink" />
          Workflows
        </a>
         <a href="#" className="flex items-center p-3 text-gpt-gray-300 rounded-lg hover:bg-gpt-gray-700/50">
          <BrainCircuit className="w-5 h-5 mr-3 text-anthropic-orange" />
          Knowledge Hub
        </a>
      </nav>
      <div className="mt-auto space-y-2">
         <a href="#" className="flex items-center p-3 text-gpt-gray-300 rounded-lg hover:bg-gpt-gray-700/50">
          <KeyRound className="w-5 h-5 mr-3" />
          API Key Vault
        </a>
        <a href="#" className="flex items-center p-3 text-gpt-gray-300 rounded-lg hover:bg-gpt-gray-700/50">
          <Settings className="w-5 h-5 mr-3" />
          Settings
        </a>
      </div>
    </aside>
  );
}
