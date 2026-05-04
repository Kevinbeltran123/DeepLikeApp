// Mirror of backend/app/domain/events.py
// Adding a new event type requires updating both files.

export type ModeId = 'pipeline' | 'monoagent' | 'multiagent';

export interface ModeInfo {
  id: ModeId;
  name: string;
  description: string;
  streams_tokens: boolean;
  streams_steps: boolean;
}

export interface TokenEvent {
  type: 'token';
  content: string;
}

export interface DetectedLangEvent {
  type: 'detected_lang';
  code: string;
  display: string;
}

export interface AgentStartEvent {
  type: 'agent_start';
  agent: string;
  icon: string;
  message: string;
}

export interface AgentActionEvent {
  type: 'agent_action';
  step: number;
  tool: string;
  icon: string;
  input: string;
}

export interface AgentObservationEvent {
  type: 'agent_observation';
  step: number;
  tool: string;
  result: string;
}

export interface AgentDoneEvent {
  type: 'agent_done';
  agent: string;
  icon: string;
  result: string;
  metadata: Record<string, unknown>;
}

export interface FinalEvent {
  type: 'final';
  translation: string;
  metadata: Record<string, unknown>;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export type StreamEvent =
  | TokenEvent
  | DetectedLangEvent
  | AgentStartEvent
  | AgentActionEvent
  | AgentObservationEvent
  | AgentDoneEvent
  | FinalEvent
  | ErrorEvent;

export interface TranslateRequest {
  text: string;
  source_lang: string;
  target_lang: string;
}
