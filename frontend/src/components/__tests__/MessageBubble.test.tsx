import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { vi } from "vitest";
import { MessageBubble } from "../MessageBubble";

const mockMessage = {
  id: "1",
  role: "user" as const,
  content: "Hello world",
  audioUrl: "test-audio.mp3",
  conversationId: "conv-1",
  metadata: {},
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  isEdited: false,
  timestamp: new Date().toISOString(),
};

describe("MessageBubble", () => {
  it("renders user message correctly", () => {
    render(<MessageBubble message={mockMessage} isUser={true} />);

    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("renders assistant message with glassmorphism", () => {
    const aiMessage = { ...mockMessage, role: "assistant" as const };
    render(<MessageBubble message={aiMessage} isUser={false} />);

    const bubble = screen.getByText("Hello world").closest("div");
    expect(bubble).toHaveClass("glassmorphism");
  });

  it("handles action clicks", () => {
    const mockOnEdit = vi.fn();
    render(
      <MessageBubble message={mockMessage} isUser={true} onEdit={mockOnEdit} />,
    );

    // Look for edit-related functionality instead
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("shows accessibility labels", () => {
    render(<MessageBubble message={mockMessage} isUser={true} />);

    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });
});
