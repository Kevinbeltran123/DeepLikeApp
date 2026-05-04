import { useEffect, useRef, useState } from 'react';
import type { TraceEntry } from '../hooks/useTranslationStream';

const SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

const pad2 = (n: number) => n.toString().padStart(2, '0');
const formatTime = (date: Date | undefined): string =>
  date ? `${pad2(date.getHours())}:${pad2(date.getMinutes())}:${pad2(date.getSeconds())}` : '--:--:--';

const truncate = (s: string, max = 130) => (s.length > max ? `${s.slice(0, max)}…` : s);

const formatArg = (input: string): string => {
  const trimmed = input.trim();
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) return truncate(input);
  return `"${truncate(input)}"`;
};

interface Props {
  trace: TraceEntry[];
  status: 'idle' | 'streaming' | 'done' | 'error';
}

export const ReactTerminal = ({ trace, status }: Props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const arrivalsRef = useRef<Date[]>([]);
  const doneTimeRef = useRef<Date | null>(null);
  const [spinnerFrame, setSpinnerFrame] = useState(0);
  const [, forceRender] = useState(0);

  useEffect(() => {
    if (trace.length === 0) {
      arrivalsRef.current = [];
      doneTimeRef.current = null;
      return;
    }
    while (arrivalsRef.current.length < trace.length) {
      arrivalsRef.current.push(new Date());
    }
  }, [trace.length]);

  useEffect(() => {
    if (status === 'done' || status === 'error') {
      if (doneTimeRef.current === null) {
        doneTimeRef.current = new Date();
        forceRender((n) => n + 1);
      }
    } else {
      doneTimeRef.current = null;
    }
  }, [status]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [trace.length, status, spinnerFrame]);

  useEffect(() => {
    if (status !== 'streaming') return;
    const id = setInterval(() => setSpinnerFrame((f) => (f + 1) % SPINNER.length), 100);
    return () => clearInterval(id);
  }, [status]);

  const spinner = SPINNER[spinnerFrame];
  const isStreaming = status === 'streaming';
  const isDone = status === 'done';
  const isError = status === 'error';
  const last = trace[trace.length - 1];

  let thinkingLabel: string | null = null;
  if (isStreaming) {
    if (!last) thinkingLabel = 'inicializando...';
    else if (last.kind === 'action') thinkingLabel = 'esperando observación...';
    else if (last.kind === 'observation') thinkingLabel = 'el agente está razonando...';
    else if (last.kind === 'start') thinkingLabel = 'el agente está razonando...';
  }

  return (
    <div className="terminal" ref={containerRef}>
      <div className="t-line">
        <span className="t-time" />
        <span className="t-prompt">agent$</span>
        <span className="t-cmd"> monoagent</span>
        {trace.length === 0 && !isStreaming && <span className="t-cursor">▌</span>}
      </div>

      {trace.map((event, i) => {
        const time = formatTime(arrivalsRef.current[i]);
        if (event.kind === 'start') {
          return (
            <div key={i} className="t-line">
              <span className="t-time">[{time}]</span>
              <span className="t-prompt">▸</span>
              <span className="t-text"> start</span>
              <span className="t-comment"> # iniciando bucle ReAct</span>
            </div>
          );
        }
        if (event.kind === 'action') {
          return (
            <div key={i} className="t-line">
              <span className="t-time">[{time}]</span>
              <span className="t-arrow">→</span>
              <span className="t-tool"> {event.tool}</span>
              <span className="t-paren">(</span>
              <span className="t-arg">{formatArg(event.input)}</span>
              <span className="t-paren">)</span>
            </div>
          );
        }
        if (event.kind === 'observation') {
          return (
            <div key={i} className="t-line">
              <span className="t-time">[{time}]</span>
              <span className="t-result">←</span>
              <span className="t-text"> {truncate(event.result)}</span>
            </div>
          );
        }
        return null;
      })}

      {thinkingLabel && (
        <div className="t-line t-think">
          <span className="t-time" />
          <span className="t-spinner">{spinner}</span>
          <span> {thinkingLabel}</span>
        </div>
      )}

      {isDone && (
        <div className="t-line">
          <span className="t-time">[{formatTime(doneTimeRef.current ?? undefined)}]</span>
          <span className="t-success">▸ done ✓</span>
        </div>
      )}

      {isError && (
        <div className="t-line">
          <span className="t-time">[{formatTime(doneTimeRef.current ?? undefined)}]</span>
          <span className="t-error">✗ error</span>
        </div>
      )}
    </div>
  );
};
