// Socket.IO client for real-time events (presence, typing)
import { io, Socket } from 'socket.io-client'

export interface PresenceEvent {
  userId: string
  status: 'online' | 'offline' | 'away'
  lastActive?: string
}

export interface TypingEvent {
  conversationId: string
  userId: string
  isTyping: boolean
}

export class RealtimeService {
  private socket: Socket

  constructor(url: string, token?: string) {
    this.socket = io(url, {
      transports: ['websocket'],
      auth: token ? { token } : undefined,
      autoConnect: true,
    })
  }

  onPresence(cb: (event: PresenceEvent) => void) {
    this.socket.on('presence', cb)
  }

  onTyping(cb: (event: TypingEvent) => void) {
    this.socket.on('typing', cb)
  }

  emitTyping(conversationId: string, isTyping: boolean) {
    this.socket.emit('typing', { conversationId, isTyping })
  }

  disconnect() {
    this.socket.disconnect()
  }
}

// Usage example (in a React hook or service):
// const rts = new RealtimeService(process.env.NEXT_PUBLIC_WS_URL, token)
// rts.onPresence(...)
// rts.onTyping(...)
// rts.emitTyping(conversationId, true)
