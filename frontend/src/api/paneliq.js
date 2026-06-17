import axios from 'axios';

const port = window.paneliqDesktop?.backendPort || 8000;
const BASE = `http://127.0.0.1:${port}`;

// Ask a question — streaming SSE pipeline.
// onEvent(event) is called for each SSE event: sql_chunk, sql_done, status,
// data, summary_chunk, summary_done, chart, error, done.
export async function askQuestionStream(question, onEvent, signal) {
  const res = await fetch(`${BASE}/ask/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6));
          onEvent(event);
          if (event.type === 'done') return;
        } catch (_) {}
      }
    }
  }
}

// Get prompt suggestions as user types
export async function getSuggestions(partial) {
  if (!partial || partial.length < 3) return [];
  const res = await axios.post(`${BASE}/suggest`, { partial });
  return res.data.suggestions || [];
}

// Health check
export async function checkHealth() {
  const res = await axios.get(`${BASE}/health`);
  return res.data;
}