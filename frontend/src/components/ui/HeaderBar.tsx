import React from 'react';

const HeaderBar: React.FC = () => {
  return (
    <header className="bg-copilot-blue h-16 flex items-center justify-between px-6 text-white">
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-bold text-cartrita-blue">Cartrita AI OS</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm">Voice Status:</span>
          <div className="w-3 h-3 bg-fuschia-pink rounded-full animate-pulse-fuschia"></div>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <select className="bg-copilot-blue-light border border-gray-600 rounded px-3 py-1 text-sm">
          <option>gpt-4.1 (Supervisor)</option>
          <option>gpt-5 (Sub-agents)</option>
        </select>
        <div className="w-8 h-8 bg-cartrita-blue rounded-full"></div>
      </div>
    </header>
  );
};

export default HeaderBar;