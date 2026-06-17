import axios from 'axios';

const port = window.paneliqDesktop?.backendPort || 8000;
const BASE = `http://127.0.0.1:${port}`;

// Ask a question — streaming SSE pipeline via XHR (more reliable than fetch
// in Electron's file:// renderer context where res.body can be null).
// onEvent(event) is called for each SSE event as it arrives.
export function askQuestionStream(question, onEvent, signal) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}/ask/stream`);
    xhr.setRequestHeader('Content-Type', 'application/json');

    let buffer = '';
    let processed = 0;
    let selfAborted = false;

    xhr.onprogress = () => {
      buffer += xhr.responseText.slice(processed);
      processed = xhr.responseText.length;

      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';

      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            onEvent(event);
            if (event.type === 'done') {
              selfAborted = true;
              xhr.abort();
              resolve();
              return;
            }
          } catch (_) {}
        }
      }
    };

    xhr.onload = () => resolve();

    xhr.onerror = () =>
      reject(new Error('Could not reach the backend. Is the server running?'));

    xhr.onabort = () => {
      if (!selfAborted)
        reject(Object.assign(new Error('Aborted'), { name: 'AbortError' }));
    };

    signal?.addEventListener('abort', () => {
      selfAborted = false; // user-initiated — treat as abort
      xhr.abort();
    });

    xhr.send(JSON.stringify({ question }));
  });
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