const REQUEST_TIMEOUT_MS = 30000;

export async function askQuestion(question) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The request timed out. Please try again.");
    }
    throw new Error("Could not reach the server. Please make sure the backend is running.");
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function checkBackendHealth() {
  try {
    const response = await fetch("/health", { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}
