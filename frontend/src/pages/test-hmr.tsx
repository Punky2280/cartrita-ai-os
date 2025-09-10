import React from 'react';

// Simple test page to satisfy Next.js module validation during builds
export default function TestHMR() {
	return (
		<div style={{ padding: 16 }}>
			<h1>HMR Test</h1>
			<p>This page exists for build-time validation. Safe to keep or remove.</p>
		</div>
	);
}
