import type { ModeId, ModeInfo, StreamEvent, TranslateRequest } from '../types/events';

const API_BASE = '/api';

export const fetchLanguages = async (): Promise<Record<string, string>> => {
  const res = await fetch(`${API_BASE}/languages`);
  if (!res.ok) throw new Error(`Failed to fetch languages: ${res.status}`);
  return res.json();
};

export const fetchModes = async (): Promise<ModeInfo[]> => {
  const res = await fetch(`${API_BASE}/modes`);
  if (!res.ok) throw new Error(`Failed to fetch modes: ${res.status}`);
  return res.json();
};

export interface HealthInfo {
  status: string;
  model: string;
  ollama_reachable: boolean;
  available_models: string[];
}

export const fetchHealth = async (): Promise<HealthInfo> => {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Failed to fetch health: ${res.status}`);
  return res.json();
};

/**
 * Streams SSE events from one of the translation endpoints.
 * The browser's EventSource only supports GET, so we hand-parse the SSE stream
 * coming back from the POST request using fetch + ReadableStream.
 */
export async function* streamTranslation(
  mode: ModeId,
  request: TranslateRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent, void, void> {
  const res = await fetch(`${API_BASE}/${mode}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Translation request failed (${res.status}): ${detail}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line.startsWith('data:')) continue;
        const payload = line.slice(5).trim();
        if (payload === '[DONE]') return;
        if (!payload) continue;
        try {
          yield JSON.parse(payload) as StreamEvent;
        } catch {
          // Skip malformed lines silently — keeps the stream going if a single
          // chunk is corrupted.
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
