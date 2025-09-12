import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import MessageList, { ChatMessage } from '../MessageList'

const msgs: ChatMessage[] = Array.from({ length: 200 }).map((_, i) => ({
  id: String(i),
  role: i % 2 === 0 ? 'user' : 'assistant',
  content: i % 5 === 0 ? '```js\nconsole.log(1)\n```' : `hello ${i}`
}))

describe('MessageList', () => {
  it('renders with virtualization container', () => {
    render(<div style={{ height: 300 }}><MessageList messages={msgs} fontSize="md" autoScroll={false} /></div>)
    const log = screen.getByRole('log')
    expect(log).toBeInTheDocument()
  })

  it('renders some messages in view', () => {
    render(<div style={{ height: 300 }}><MessageList messages={msgs} fontSize="md" autoScroll={false} /></div>)
    // Should render at least one role label
    expect(screen.getAllByText(/user|assistant/i).length).toBeGreaterThan(0)
  })
})
