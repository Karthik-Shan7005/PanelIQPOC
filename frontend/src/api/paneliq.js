import axios from 'axios';

const port = window.paneliqDesktop?.backendPort || 8000;
const BASE = `http://127.0.0.1:${port}`;

// Ask a question — full pipeline. Pass an AbortController signal to cancel.
export async function askQuestion(question, signal) {
  const res = await axios.post(`${BASE}/ask`, { question }, { signal });
  return res.data;
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