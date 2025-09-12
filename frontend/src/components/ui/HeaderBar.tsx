import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Activity } from 'lucide-react';
import Link from 'next/link';

const HeaderBar: React.FC = () => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 h-16 flex items-center justify-between px-6 text-white shadow-2xl border-b border-purple-500/20"
    >
      <div className="flex items-center space-x-6">
        <motion.div
          className="flex items-center space-x-3"
          whileHover={{ scale: 1.05 }}
        >
          <div className="relative">
            <Zap className="h-8 w-8 text-yellow-400" />
            <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-500 bg-clip-text text-transparent">
            DAT-BITCH-CARTRITA
          </h1>
        </motion.div>

        <div className="hidden md:flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full backdrop-blur-sm">
            <Activity className="h-4 w-4 text-green-400" />
            <span className="text-sm font-medium">AI Active</span>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full backdrop-blur-sm">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            <span className="text-sm">Multi-Agent</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <Link
          href="/about"
          className="px-3 py-1.5 rounded-lg bg-white/10 border border-white/20 text-sm hover:bg-white/20 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-400"
        >
          About
        </Link>
        <motion.select
          whileHover={{ scale: 1.02 }}
          className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-sm backdrop-blur-sm hover:bg-white/20 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-400"
        >
          <option className="bg-gray-800">GPT-4.1 (Supervisor)</option>
          <option className="bg-gray-800">GPT-5 (Sub-agents)</option>
          <option className="bg-gray-800">GPT-4o</option>
        </motion.select>

        <motion.div
          className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center cursor-pointer shadow-lg"
          whileHover={{ scale: 1.1, rotate: 5 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="text-white font-bold text-lg">C</span>
        </motion.div>
      </div>
    </motion.header>
  );
};

export default HeaderBar;