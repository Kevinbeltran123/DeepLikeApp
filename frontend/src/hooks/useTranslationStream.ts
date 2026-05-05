import { useCallback, useRef, useState } from 'react';
import type {
  AgentActionEvent,
  AgentDoneEvent,
  AgentObservationEvent,
  AgentStartEvent,
  AgentThoughtEvent,
  AgentWarningEvent,
  ModeId,
  StreamEvent,
  TranslateRequest,
} from '../types/events';
import { streamTranslation } from '../services/translationApi';

export type TraceEntry =
  | (AgentStartEvent & { kind: 'start' })
  | (AgentActionEvent & { kind: 'action' })
  | (AgentObservationEvent & { kind: 'observation' })
  | (AgentThoughtEvent & { kind: 'thought' })
  | (AgentWarningEvent & { kind: 'warning' })
  | (AgentDoneEvent & { kind: 'done' });

export interface TranslationState {
  status: 'idle' | 'streaming' | 'done' | 'error';
  translation: string;
  detectedLang: { code: string; display: string } | null;
  trace: TraceEntry[];
  error: string | null;
  finalMetadata: Record<string, unknown> | null;
}

const initialState: TranslationState = {
  status: 'idle',
  translation: '',
  detectedLang: null,
  trace: [],
  error: null,
  finalMetadata: null,
};

export const useTranslationStream = () => {
  const [state, setState] = useState<TranslationState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => setState(initialState), []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const translate = useCallback(async (mode: ModeId, request: TranslateRequest) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ ...initialState, status: 'streaming' });

    try {
      for await (const event of streamTranslation(mode, request, controller.signal)) {
        setState((prev) => applyEvent(prev, event));
      }
      setState((prev) => (prev.status === 'error' ? prev : { ...prev, status: 'done' }));
    } catch (err: unknown) {
      if ((err as { name?: string })?.name === 'AbortError') return;
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Unknown error',
      }));
    } finally {
      abortRef.current = null;
    }
  }, []);

  return { state, translate, reset, cancel };
};

const applyEvent = (state: TranslationState, event: StreamEvent): TranslationState => {
  switch (event.type) {
    case 'token':
      return { ...state, translation: state.translation + event.content };
    case 'detected_lang':
      return { ...state, detectedLang: { code: event.code, display: event.display } };
    case 'agent_start':
      return { ...state, trace: [...state.trace, { ...event, kind: 'start' }] };
    case 'agent_action':
      return { ...state, trace: [...state.trace, { ...event, kind: 'action' }] };
    case 'agent_observation':
      return { ...state, trace: [...state.trace, { ...event, kind: 'observation' }] };
    case 'agent_thought':
      return { ...state, trace: [...state.trace, { ...event, kind: 'thought' }] };
    case 'agent_warning':
      return { ...state, trace: [...state.trace, { ...event, kind: 'warning' }] };
    case 'agent_done':
      return { ...state, trace: [...state.trace, { ...event, kind: 'done' }] };
    case 'final':
      return {
        ...state,
        translation: event.translation || state.translation,
        finalMetadata: event.metadata,
      };
    case 'error':
      return { ...state, status: 'error', error: event.message };
    default:
      return state;
  }
};
