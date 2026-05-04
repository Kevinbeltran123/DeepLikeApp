import { useEffect, useState } from 'react';
import type { TraceEntry } from '../hooks/useTranslationStream';
import { Icon } from './icons';

interface Station {
  name: string;
  label: string;
  icon: string;
}

const STATIONS: Station[] = [
  { name: 'detector', label: 'Detector', icon: 'search' },
  { name: 'terminologo', label: 'Terminólogo', icon: 'book' },
  { name: 'traductor', label: 'Traductor', icon: 'globe' },
  { name: 'revisor', label: 'Revisor', icon: 'check' },
];

type StationStatus = 'pending' | 'doing' | 'done';

interface StationState extends Station {
  status: StationStatus;
  startMessage?: string;
  doneResult?: string;
}

const deriveStations = (trace: TraceEntry[]): StationState[] =>
  STATIONS.map((s) => {
    const start = trace.find((t) => t.kind === 'start' && t.agent === s.name);
    const done = trace.find((t) => t.kind === 'done' && t.agent === s.name);
    if (done && done.kind === 'done') {
      return {
        ...s,
        status: 'done',
        startMessage: start && start.kind === 'start' ? start.message : undefined,
        doneResult: done.result,
      };
    }
    if (start && start.kind === 'start') {
      return { ...s, status: 'doing', startMessage: start.message };
    }
    return { ...s, status: 'pending' };
  });

const findAutoFocus = (stations: StationState[]): number => {
  const doingIdx = stations.findIndex((s) => s.status === 'doing');
  if (doingIdx !== -1) return doingIdx;
  let lastDone = -1;
  stations.forEach((s, i) => {
    if (s.status === 'done') lastDone = i;
  });
  return lastDone;
};

interface Props {
  trace: TraceEntry[];
}

export const OrchestratorSubway = ({ trace }: Props) => {
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    if (trace.length === 0) setSelected(null);
  }, [trace.length]);

  const stations = deriveStations(trace);
  const autoFocus = findAutoFocus(stations);
  const focused = selected ?? autoFocus;
  const focusedStation = focused >= 0 ? stations[focused] : null;
  const orchestratorStarted = trace.some((t) => t.kind === 'start' && t.agent === 'orchestrator');

  const lastActiveIdx = stations.reduce(
    (acc, s, i) => (s.status !== 'pending' ? i : acc),
    -1,
  );
  const progress = lastActiveIdx <= 0 ? 0 : (lastActiveIdx / (STATIONS.length - 1)) * 100;

  if (trace.length === 0) {
    return (
      <div className="subway empty">
        <span className="placeholder">Los pasos de los agentes aparecerán aquí…</span>
      </div>
    );
  }

  return (
    <div className="subway">
      {orchestratorStarted && (
        <div className="subway-orchestrator">
          <span className="spark"><Icon name="spark" /></span>
          <span>Orchestrator coordinando {STATIONS.length} agentes en serie</span>
        </div>
      )}

      <div
        className="subway-track"
        style={
          {
            '--stations': STATIONS.length,
            '--progress': `${progress}%`,
          } as React.CSSProperties
        }
      >
        {stations.map((s, idx) => (
          <button
            key={s.name}
            type="button"
            className={`subway-station ${s.status} ${idx === focused ? 'focused' : ''}`}
            onClick={() => setSelected(idx)}
            aria-label={`${s.label}: ${s.status}`}
            aria-pressed={idx === focused}
          >
            <span className="subway-node">
              {s.status === 'done' ? <Icon name="check" /> : <Icon name={s.icon} />}
            </span>
            <span className="subway-label">{s.label}</span>
            <span className="subway-status">
              {s.status === 'doing' ? 'en curso' : s.status === 'done' ? 'listo' : '—'}
            </span>
          </button>
        ))}
      </div>

      <SubwayDetail station={focusedStation} />
    </div>
  );
};

const SubwayDetail = ({ station }: { station: StationState | null }) => {
  if (!station) {
    return (
      <div className="subway-detail empty">
        <span>Esperando inicio del pipeline…</span>
      </div>
    );
  }

  return (
    <div className={`subway-detail ${station.status}`}>
      <div className="subway-detail-header">
        <span className="subway-detail-icon"><Icon name={station.icon} /></span>
        <span className="subway-detail-name">{station.label}</span>
        <span className={`subway-detail-status ${station.status}`}>
          {station.status === 'doing'
            ? 'en progreso'
            : station.status === 'done'
              ? 'completado'
              : 'pendiente'}
        </span>
      </div>
      {station.status === 'pending' && (
        <span className="subway-detail-message">Aún no comienza.</span>
      )}
      {station.status === 'doing' && station.startMessage && (
        <span className="subway-detail-message">{station.startMessage}</span>
      )}
      {station.status === 'done' && (
        <>
          {station.startMessage && (
            <span className="subway-detail-message">{station.startMessage}</span>
          )}
          {station.doneResult && (
            <p className="subway-detail-result">{station.doneResult}</p>
          )}
        </>
      )}
    </div>
  );
};
