import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { MessageBubble } from '../MessageBubble';

const mockMessage = {
  id: '1',
  role: 'user' as const,
  content: 'Hello world',
  audioUrl: 'test-audio.mp3',
  conversationId: 'conv-1',
  metadata: {},
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  isEdited: false,
  timestamp: new Date().toISOString()
};

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    render(<MessageBubble message={mockMessage} onAction={vi.fn()} />);
    
    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
  });

  it('renders assistant message with glassmorphism', () => {
    const aiMessage = { ...mockMessage, role: 'assistant' as const };
    render(<MessageBubble message={aiMessage} onAction={vi.fn()} />);
    
    const bubble = screen.getByText('Hello world').closest('div');
    expect(bubble).toHaveClass('glassmorphism');
  });

  it('handles action clicks', () => {
    const mockOnAction = vi.fn();
    render(<MessageBubble message={mockMessage} onAction={mockOnAction} />);
    
    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);
    
    expect(mockOnAction).toHaveBeenCalledWith('copy');
  });

  it('shows accessibility labels', () => {
    render(<MessageBubble message={mockMessage} onAction={vi.fn()} />);
    
    const playButton = screen.getByRole('button', { name: /play audio/i });
    expect(playButton).toBeInTheDocument();
  });
});
