import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider as JotaiProvider } from "jotai";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "../MessageBubble";

function renderWithProviders(ui: React.ReactNode) {
	const client = new QueryClient();
	return render(
		<QueryClientProvider client={client}>
			<JotaiProvider>{ui}</JotaiProvider>
		</QueryClientProvider>,
	);
}

describe("MessageBubble (integration)", () => {
	it("renders without crashing", () => {
		const msg = {
			id: "int-1",
			role: "user" as const,
			content: "Integration hello",
			audioUrl: null,
			conversationId: "conv-int",
			metadata: {},
			createdAt: new Date().toISOString(),
			updatedAt: new Date().toISOString(),
			isEdited: false,
			timestamp: new Date().toISOString(),
		};
		renderWithProviders(<MessageBubble message={msg} isUser={true} />);
		expect(screen.getByText("Integration hello")).toBeInTheDocument();
	});
});
