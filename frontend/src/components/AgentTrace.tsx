import type { TraceEntry } from '../hooks/useTranslationStream';
import { Icon } from './icons';
import { OrchestratorSubway } from './OrchestratorSubway';
import { ReactTerminal } from './ReactTerminal';

interface Props {
  trace: TraceEntry[];
  variant: 'monoagent' | 'multiagent';
  status: 'idle' | 'streaming' | 'done' | 'error';
}

export const AgentTrace = ({ trace, variant, status }: Props) =>
  variant === 'multiagent'
    ? <OrchestratorSubway trace={trace} />
    : <ReactTerminal trace={trace} status={status} />;

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
