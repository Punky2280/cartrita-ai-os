// Next.js API Route - Conversations API
// Handles conversation management

import type { NextApiRequest, NextApiResponse } from 'next'
import type { ApiResponse, Conversation } from '@/types'
import { createApiResponse, handleApiError } from '@/utils'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const apiKey = 'dev-api-key-2025'

    if (req.method === 'GET') {
      // Get conversations list
      const conversations: Conversation[] = [
        {
          id: 'default-conversation',
          title: 'New Chat',
          messages: [],
          agentId: 'supervisor',
          workspaceId: undefined,
          userId: 'default-user',
          isArchived: false,
          isPinned: false,
          tags: [],
          metadata: {
          totalMessages: 0,
          lastActivity: new Date().toISOString(),
          agentUsed: 'supervisor',
          tokensUsed: 0,
          processingTime: 0
        },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          lastMessageAt: new Date().toISOString()
        }
      ]

      const response: ApiResponse<Conversation[]> = createApiResponse(true, conversations, undefined, 'Conversations retrieved successfully')
      res.status(200).json(response)
    } else if (req.method === 'POST') {
      // Create new conversation
      const { title, agentId, workspaceId, initialMessage } = req.body

      const newConversation: Conversation = {
        id: `conversation-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        title: title || 'New Chat',
        messages: [],
        agentId: agentId || 'supervisor',
        workspaceId,
        userId: 'default-user',
        isArchived: false,
        isPinned: false,
        tags: [],
        metadata: {
          totalMessages: 0,
          lastActivity: new Date().toISOString(),
          agentUsed: agentId || 'supervisor',
          tokensUsed: 0,
          processingTime: 0
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        lastMessageAt: new Date().toISOString()
      }

      const response: ApiResponse<Conversation> = createApiResponse(true, newConversation, undefined, 'Conversation created successfully')
      res.status(201).json(response)
    } else {
      res.setHeader('Allow', ['GET', 'POST'])
      res.status(405).json(handleApiError(new Error('Method not allowed')))
    }
  } catch (error) {
    console.error('Conversations API error:', error)
    res.status(500).json(handleApiError(error as Error))
  }
}