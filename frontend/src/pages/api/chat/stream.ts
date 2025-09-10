// Next.js API Route - Chat Streaming Proxy
// Handles authentication and proxies requests to backend

import type { NextApiRequest, NextApiResponse } from 'next'
import httpProxy from 'http-proxy'

// Create the proxy server
const proxy = httpProxy.createProxyServer()

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  return new Promise<void>((resolve, reject) => {
    // Add API key to request headers from environment (EventSource cannot send headers; proxy injects)
    const apiKey = process.env.BACKEND_API_KEY || process.env.AI_API_KEY || ''
    if (apiKey) {
      req.headers['x-api-key'] = apiKey
    }
    
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
    
    if (req.method === 'OPTIONS') {
      res.status(200).end()
      resolve()
      return
    }

    proxy.web(req, res, {
      target: process.env.BACKEND_BASE_URL || 'http://localhost:8000',
      changeOrigin: true,
      selfHandleResponse: false,
      timeout: 70000
    }, (err) => {
      if (err) {
        console.error('Proxy error:', err)
        
        // Check if it's a connection error (backend not running)
        if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
          res.status(503).json({ 
            error: 'Backend unavailable', 
            details: 'AI service is not running. Please start the backend services.',
            code: 'BACKEND_DOWN'
          })
        } else {
          res.status(500).json({ 
            error: 'Proxy failed', 
            details: err.message,
            code: err.code || 'PROXY_ERROR'
          })
        }
        reject(err)
      } else {
        resolve()
      }
    })
  })
}

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
  },
}