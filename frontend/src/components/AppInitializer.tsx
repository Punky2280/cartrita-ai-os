// Cartrita AI OS - App Initializer
// Handles initial state setup and data loading

import { useEffect } from 'react'
import { useSetAtom } from 'jotai'
import {
  agentsAtom,
  selectedAgentIdAtom,
  conversationsAtom,
  userAtom,
  authTokenAtom
} from '@/stores'
import { apiClient } from '@/services/api'
import type { Agent } from '@/types'

const defaultAgents: Agent[] = [
  {
    id: 'supervisor',
    name: 'Cartrita Supervisor',
    type: 'supervisor',
    status: 'idle',
    model: 'gpt-4',
    description: 'Intelligent task orchestrator with multi-agent delegation capabilities',
    capabilities: ['task_planning', 'agent_orchestration', 'decision_making', 'context_management'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  },
  {
    id: 'research',
    name: 'Research Agent',
    type: 'research',
    status: 'idle',
    model: 'gpt-4',
    description: 'Advanced web search and information synthesis specialist',
    capabilities: ['web_search', 'data_analysis', 'information_synthesis', 'fact_checking'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  },
  {
    id: 'code',
    name: 'Code Agent',
    type: 'code',
    status: 'idle',
    model: 'gpt-4',
    description: 'Software development and programming expert',
    capabilities: ['code_generation', 'debugging', 'code_review', 'architecture_design'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  },
  {
    id: 'computer_use',
    name: 'Computer Use Agent',
    type: 'computer_use',
    status: 'idle',
  model: 'gpt-4o-mini',
    description: 'System interaction and automation specialist',
    capabilities: ['computer_control', 'file_management', 'system_automation', 'tool_usage'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  },
  {
    id: 'knowledge',
    name: 'Knowledge Agent',
    type: 'knowledge',
    status: 'idle',
    model: 'gpt-4',
    description: 'Document analysis and knowledge base specialist',
    capabilities: ['document_analysis', 'knowledge_extraction', 'rag_search', 'content_generation'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  },
  {
    id: 'task',
    name: 'Task Agent',
    type: 'task',
    status: 'idle',
    model: 'gpt-4',
    description: 'Project management and task coordination expert',
    capabilities: ['project_planning', 'task_management', 'progress_tracking', 'coordination'],
    last_used_at: new Date().toISOString(),
    usage_count: 0,
    metadata: {
      version: '2.0',
      uptime: 0,
      memory_usage: 0,
      queue_size: 0,
      totalRequests: 0,
      successRate: 1.0,
      avgLatency: 0,
      lastActive: new Date().toISOString()
    }
  }
]

export default function AppInitializer() {
  const setAgents = useSetAtom(agentsAtom)
  const setSelectedAgentId = useSetAtom(selectedAgentIdAtom)
  const setConversations = useSetAtom(conversationsAtom)
  const setUser = useSetAtom(userAtom)
  const setAuthToken = useSetAtom(authTokenAtom)

  useEffect(() => {
    // Initialize agents immediately
    setAgents(defaultAgents)
    setSelectedAgentId('supervisor') // Default to supervisor

    // Set up a development user
    const devUser = {
      id: 'dev-user-1',
      email: 'developer@cartrita.ai',
      name: 'Developer',
      preferences: {
        theme: 'dark' as const,
        language: 'en',
        notifications: {
          email: false,
          push: false,
          sound: true,
          desktop: true
        },
        privacy: {
          dataCollection: false,
          saveHistory: true,
          profileVisibility: false,
          showActivity: false
        },
        accessibility: {
          highContrast: false,
          reducedMotion: false,
          fontSize: 'medium' as const,
          screenReader: false
        }
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isActive: true,
      role: 'user' as const
    }

    // Set development user
    setUser(devUser)
    
    // Set a development token
    const devToken = 'dev-key-cartrita-ai-os'
    setAuthToken(devToken)
    apiClient.setAuthToken(devToken)

    // Initialize empty conversations
    setConversations([])

    // Try to fetch real data from the API (if available)
    const initializeRealData = async () => {
      try {
        // Test health endpoint first
        const health = await apiClient.getHealthStatus()
        if (health.success) {
          console.log('API is healthy, loading real data...')

          // Try to load real agents
          try {
            const agentsResponse = await apiClient.getAgents()
            if (agentsResponse.success && agentsResponse.data) {
              setAgents(agentsResponse.data)
            }
          } catch {
            console.warn('Failed to load agents from API, using defaults')
          }

          // Try to load conversations
          try {
            const conversationsResponse = await apiClient.getConversations()
            if (conversationsResponse.success && conversationsResponse.data) {
              setConversations(conversationsResponse.data)
            }
          } catch {
            console.warn('Failed to load conversations from API')
          }
        }
      } catch (error) {
        console.warn('API not available, using mock data:', error)
        // Continue with mock data - this is expected in development
      }
    }

    // Initialize real data after a brief delay
    setTimeout(initializeRealData, 1000)

  }, [setAgents, setSelectedAgentId, setConversations, setUser, setAuthToken])

  // This component doesn't render anything
  return null
}