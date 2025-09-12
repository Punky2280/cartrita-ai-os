// Next.js API Route - Voice Transcription Proxy
// Proxies POST /api/voice/transcribe

import type { NextApiRequest, NextApiResponse } from 'next'
import httpProxy from 'http-proxy'

const proxy = httpProxy.createProxyServer()

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  return new Promise<void>((resolve, reject) => {
    const apiKey = process.env.BACKEND_API_KEY || process.env.AI_API_KEY || ''
    if (apiKey) {
      req.headers['x-api-key'] = apiKey
      req.headers['authorization'] = `Bearer ${apiKey}`
    }

    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS')
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')

    if (req.method === 'OPTIONS') {
      res.status(200).end()
      resolve()
      return
    }

    if (req.method !== 'POST') {
      res.status(405).json({ error: 'Method Not Allowed' })
      resolve()
      return
    }

    proxy.web(
      req,
      res,
      {
        target: process.env.BACKEND_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
        selfHandleResponse: false,
        timeout: 35000,
      },
      (err: any) => {
        console.error('Proxy error:', err)
        if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
          res.status(503).json({ error: 'Backend unavailable', details: 'AI service is not running. Please start the backend services.', code: 'BACKEND_DOWN' })
        } else {
          res.status(500).json({ error: 'Proxy failed', details: err.message, code: err.code || 'PROXY_ERROR' })
        }
        reject(err)
      }
    )
  })
}

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
  },
}
