// Cartrita AI OS - Main Landing Page
// Modern landing experience with direct access to chat interface

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import dynamic from "next/dynamic";
import { useAtomValue } from "jotai";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Bot,
  Zap,
  Shield,
  Sparkles,
  Brain,
  Layers,
  Cpu,
} from "lucide-react";
import { isAuthenticatedAtom, userAtom } from "@/stores";
import { cn } from "@/utils";
import ConnectionTest from "@/components/ConnectionTest";

function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component is mounted before using client-side features
  useEffect(() => {
    setIsMounted(true);
    setIsLoading(false);
  }, []);

  const handleGetStarted = () => {
    if (isMounted) {
      router.push("/ChatInterface");
    }
  };

  const handleLearnMore = () => {
    if (isMounted) {
      router.push("/about");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white overflow-hidden relative">
      {/* Neural Network Background */}
      <div className="absolute inset-0 opacity-40">
        <img
          src="/neural-pattern.svg"
          alt=""
          className="w-full h-full object-cover"
        />
      </div>

      {/* Enhanced Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-96 h-96 bg-gradient-to-br from-purple-600/15 via-blue-600/10 to-transparent rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute bottom-20 right-20 w-[500px] h-[500px] bg-gradient-to-tl from-cyan-500/15 via-blue-500/10 to-transparent rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-gradient-to-r from-pink-500/8 via-purple-500/8 to-blue-500/8 rounded-full blur-3xl" />

        {/* Additional floating orbs */}
        <div
          className="absolute top-1/4 right-1/4 w-32 h-32 bg-purple-400/10 rounded-full blur-2xl animate-pulse"
          style={{ animationDelay: "2s" }}
        />
        <div
          className="absolute bottom-1/4 left-1/4 w-40 h-40 bg-cyan-400/10 rounded-full blur-2xl animate-pulse"
          style={{ animationDelay: "3s" }}
        />
      </div>

      {/* Development: Connection Test */}
      <div className="fixed top-4 right-4 z-50">
        <ConnectionTest />
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="p-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="w-12 h-12 relative">
                <img
                  src="/cartrita-icon.svg"
                  alt="Cartrita AI OS Logo"
                  className="w-full h-full"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  Cartrita AI OS
                </span>
                <span className="text-xs text-gray-400 font-medium tracking-wide">
                  Neural Multi-Agent System
                </span>
              </div>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              onClick={handleGetStarted}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg hover:from-purple-500 hover:to-blue-500 transition-all duration-200 font-medium shadow-lg"
            >
              Get Started
            </motion.button>
          </div>
        </header>

        {/* Hero Section */}
        <main className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-4xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mb-8"
            >
              <div className="flex items-center justify-center mb-4">
                <div className="px-4 py-2 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-full border border-purple-500/30 backdrop-blur-sm">
                  <span className="text-sm font-medium text-purple-300">
                    ✨ Neural AI Architecture
                  </span>
                </div>
              </div>

              <h1 className="text-5xl md:text-7xl font-bold mb-6">
                <span className="bg-gradient-to-r from-white via-purple-100 to-white bg-clip-text text-transparent">
                  The Future of
                </span>
                <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent block mt-2">
                  AI Orchestration
                </span>
              </h1>
            </motion.div>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed"
            >
              Experience the most advanced AI operating system featuring
              <span className="text-purple-300 font-semibold">
                {" "}
                hierarchical multi-agent orchestration
              </span>
              , real-time voice processing, and intelligent task delegation
              powered by cutting-edge neural architecture.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
            >
              <button
                onClick={handleGetStarted}
                className="group relative px-8 py-4 bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 rounded-xl hover:from-purple-500 hover:via-blue-500 hover:to-cyan-500 transition-all duration-300 font-semibold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600/50 via-blue-600/50 to-cyan-600/50 blur-xl opacity-75 group-hover:opacity-100 transition-opacity" />
                <span className="relative flex items-center">
                  <Brain className="mr-2 w-5 h-5" />
                  Start Neural Chat
                  <ArrowRight className="inline-block ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </button>

              <button
                onClick={handleLearnMore}
                className="group px-8 py-4 border-2 border-gray-600 rounded-xl hover:border-purple-400 transition-all duration-300 font-semibold text-lg hover:bg-purple-500/10 backdrop-blur-sm relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="relative flex items-center justify-center">
                  <Layers className="mr-2 w-5 h-5" />
                  Explore Architecture
                </span>
              </button>
            </motion.div>

            {/* Features Grid */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto"
            >
              <div className="p-6 bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-700/50 hover:border-purple-500/50 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Lightning Fast</h3>
                <p className="text-gray-400">
                  Advanced streaming and real-time processing for instant
                  responses
                </p>
              </div>

              <div className="p-6 bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Secure & Private</h3>
                <p className="text-gray-400">
                  Enterprise-grade security with end-to-end encryption
                </p>
              </div>

              <div className="p-6 bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-700/50 hover:border-pink-500/50 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-r from-pink-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Multi-Agent AI</h3>
                <p className="text-gray-400">
                  Specialized agents for research, coding, and complex tasks
                </p>
              </div>
            </motion.div>
          </div>
        </main>

        {/* Footer */}
        <footer className="p-6">
          <div className="max-w-7xl mx-auto text-center text-gray-400">
            <p>
              &copy; 2025 Cartrita AI OS. Powered by advanced AI orchestration.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default dynamic(() => Promise.resolve(Home), { ssr: false });
