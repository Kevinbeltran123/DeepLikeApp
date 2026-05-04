import type { TraceEntry } from '../hooks/useTranslationStream';
import { Icon } from './icons';

interface Props {
  trace: TraceEntry[];
  variant: 'monoagent' | 'multiagent';
}

export const AgentTrace = ({ trace, variant }: Props) => {
  if (trace.length === 0) {
    return (
      <div className="agent-trace empty">
        <span className="placeholder">
          {variant === 'monoagent'
            ? 'El bucle ReAct del agente aparecera aqui...'
            : 'Los pasos de los agentes apareceran aqui...'}
        </span>
      </div>
    );
  }

  return (
    <ol className="agent-trace">
      {trace.map((entry, idx) => (
        <li key={idx} className={`trace-entry trace-${entry.kind}`}>
          <TraceItem entry={entry} />
        </li>
      ))}
    </ol>
  );
};

const TraceItem = ({ entry }: { entry: TraceEntry }) => {
  switch (entry.kind) {
    case 'start':
      return (
        <>
          <span className="trace-icon"><Icon name={entry.icon} /></span>
          <div className="trace-body">
            <strong className="trace-agent">{entry.agent}</strong>
            <span className="trace-message">{entry.message}</span>
          </div>
        </>
      );
    case 'action':
      return (
        <>
          <span className="trace-step">#{entry.step}</span>
          <span className="trace-icon"><Icon name={entry.icon} /></span>
          <div className="trace-body">
            <strong className="trace-agent">Action: {entry.tool}</strong>
            <code className="trace-input">{entry.input}</code>
          </div>
        </>
      );
    case 'observation':
      return (
        <>
          <span className="trace-step">#{entry.step}</span>
          <span className="trace-icon obs">
            <span className="dot" />
          </span>
          <div className="trace-body">
            <strong className="trace-agent">Observation</strong>
            <span className="trace-result">{entry.result}</span>
          </div>
        </>
      );
    case 'done':
      return (
        <>
          <span className="trace-icon done"><Icon name={entry.icon} /></span>
          <div className="trace-body">
            <strong className="trace-agent">{entry.agent} (done)</strong>
            <span className="trace-result">{entry.result}</span>
          </div>
        </>
      );
  }
};
