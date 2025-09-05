import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MessageBubble from '../MessageBubble';

const mockMessage = {
  id: '1',
  role: 'user' as const,
  content: 'Hello world',
  audioUrl: 'test-audio.mp3'
};

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    render(<MessageBubble message={mockMessage} onAction={jest.fn()} />);
    
    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
  });

  it('renders AI message with glassmorphism', () => {
    const aiMessage = { ...mockMessage, role: 'ai' as const };
    render(<MessageBubble message={aiMessage} onAction={jest.fn()} />);
    
    const bubble = screen.getByText('Hello world').closest('div');
    expect(bubble).toHaveClass('glassmorphism');
  });

  it('handles action clicks', () => {
    const mockOnAction = jest.fn();
    render(<MessageBubble message={mockMessage} onAction={mockOnAction} />);
    
    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);
    
    expect(mockOnAction).toHaveBeenCalledWith('copy');
  });

  it('shows accessibility labels', () => {
    render(<MessageBubble message={mockMessage} onAction={jest.fn()} />);
    
    const playButton = screen.getByRole('button', { name: /play audio/i });
    expect(playButton).toBeInTheDocument();
  });
});
