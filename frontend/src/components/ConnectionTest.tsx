import { useState, useEffect } from "react";

export default function ConnectionTest() {
  const [connectionStatus, setConnectionStatus] = useState("Testing...");
  const [healthData, setHealthData] = useState(null);
  const [chatResponse, setChatResponse] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    testConnection();
  }, []);

  const testConnection = async () => {
    const isLocalhost =
      typeof window !== "undefined" &&
      (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1");

    try {
      console.log("Testing backend connection...");

      // Test health endpoint with timeout and error handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

  // Use HTTPS in production, HTTP only for localhost. Default to API Gateway on 3001 locally.
  const defaultUrl = isLocalhost ? "http://localhost:3001" : "https://api.cartrita.ai";
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        process.env.BACKEND_BASE_URL ||
        defaultUrl;
      const healthResponse = await fetch(`${baseUrl}/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!healthResponse.ok) {
        throw new Error(`Health check failed: ${healthResponse.status}`);
      }

      const healthJson = await healthResponse.json();
      setHealthData(healthJson);
      console.log("Health check successful:", healthJson);

      // Test chat endpoint
      const chatResponse = await fetch(`${baseUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key":
            process.env.NEXT_PUBLIC_CARTRITA_API_KEY || "dev-api-key-2025",
        },
        body: JSON.stringify({
          message: "Hello from React frontend!",
          conversation_id: crypto.randomUUID(),
        }),
      });

      // For dev mode, we expect a 500 error due to OpenAI API key issues
      // As long as we get past authentication (not 401/403), the connection works
      if (chatResponse.status === 401 || chatResponse.status === 403) {
        throw new Error(`Authentication failed: ${chatResponse.status}`);
      }

      const chatJson = await chatResponse.json();
      setChatResponse(chatJson);
      console.log("Chat response received:", chatJson);

      setConnectionStatus("✅ Connection successful! (Backend reachable)");
      setError(null);
    } catch (err) {
      console.error("Connection test failed:", err);
      setConnectionStatus("❌ Connection failed");

      let errorMessage = "Unknown error occurred";
      if (err instanceof Error) {
        if (
          err.message.includes("Failed to fetch") ||
          err.name === "AbortError"
        ) {
          errorMessage =
            "Backend service is not running. Please start the stack and access the API Gateway at " +
            (isLocalhost ? "http://localhost:3001" : "your backend URL");
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
    }
  };

  return (
    <div
      style={{
        padding: "20px",
        margin: "20px",
        border: "2px solid #ccc",
        borderRadius: "8px",
        backgroundColor: "#f9f9f9",
      }}
    >
      <h2>Backend Connection Test</h2>
      <p>
        <strong>Status:</strong> {connectionStatus}
      </p>

      {error && (
        <div style={{ color: "red", marginBottom: "10px" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {healthData && (
        <div style={{ marginBottom: "10px" }}>
          <h3>Health Check Response:</h3>
          <pre style={{ backgroundColor: "#f0f0f0", padding: "10px" }}>
            {JSON.stringify(healthData, null, 2)}
          </pre>
        </div>
      )}

      {chatResponse && (
        <div>
          <h3>Chat Response:</h3>
          <pre style={{ backgroundColor: "#f0f0f0", padding: "10px" }}>
            {JSON.stringify(chatResponse, null, 2)}
          </pre>
        </div>
      )}

      <button
        onClick={testConnection}
        style={{
          padding: "10px 20px",
          backgroundColor: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        Retry Connection Test
      </button>
    </div>
  );
}
