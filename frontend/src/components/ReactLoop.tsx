import { useEffect, useRef, useState } from 'react';
import type { TraceEntry } from '../hooks/useTranslationStream';
import { Icon } from './icons';

type PhaseId = 'think' | 'act' | 'observe';

interface Phase {
  id: PhaseId;
  label: string;
  x: number;
  y: number;
  labelY: number;
}

const RING_CX = 140;
const RING_CY = 100;
const RING_RADIUS = 64;
const MIN_DWELL_MS = 650;

const PHASES: Phase[] = [
  { id: 'think',   label: 'Pensar',   x: 140, y: 36,  labelY: 22 },
  { id: 'act',     label: 'Actuar',   x: 195, y: 132, labelY: 162 },
  { id: 'observe', label: 'Observar', x: 85,  y: 132, labelY: 162 },
];

const ARROW_ANGLES = [60, 180, 300]; // degrees clockwise from top

interface Step {
  step: number;
  tool: string;
  icon: string;
  input: string;
  thoughts: string[];
  warnings: string[];
  observation?: string;
  status: 'thinking' | 'doing' | 'done';
}

const ensureStep = (steps: Step[], step: number): Step => {
  let target = steps.find((s) => s.step === step);
  if (!target) {
    target = {
      step,
      tool: '',
      icon: 'spark',
      input: '',
      thoughts: [],
      warnings: [],
      status: 'thinking',
    };
    steps.push(target);
    steps.sort((a, b) => a.step - b.step);
  }
  return target;
};

const groupSteps = (trace: TraceEntry[]): Step[] => {
  const result: Step[] = [];
  for (const e of trace) {
    if (e.kind === 'thought') {
      const target = ensureStep(result, e.step);
      target.thoughts.push(e.content);
    } else if (e.kind === 'warning') {
      const target = ensureStep(result, e.step || 1);
      target.warnings.push(e.message);
    } else if (e.kind === 'action') {
      const target = ensureStep(result, e.step);
      target.tool = e.tool;
      target.icon = e.icon;
      target.input = e.input;
      target.status = 'doing';
    } else if (e.kind === 'observation') {
      const target = ensureStep(result, e.step);
      target.observation = e.result;
      target.status = 'done';
    }
  }
  return result;
};

interface Props {
  trace: TraceEntry[];
  status: 'idle' | 'streaming' | 'done' | 'error';
}

export const ReactLoop = ({ trace, status }: Props) => {
  const animPhase = useAnimatedPhase(trace);

  if (trace.length === 0) {
    return (
      <div className="react-loop-empty">
        <span>El bucle ReAct del agente aparecerá aquí…</span>
      </div>
    );
  }

  const done = status === 'done' || status === 'error';
  const queueDrained = animPhase === null;
  const effectivePhase = done && queueDrained ? null : animPhase;
  const steps = groupSteps(trace);
  const iterations = steps.length;

  return (
    <div className="react-loop">
      <LoopDiagram activePhase={effectivePhase} iterations={iterations} done={done && queueDrained} />

      <div className="loop-steps-container">
        {steps.length === 0 ? (
          <div className="loop-steps-empty">
            <span>El agente está decidiendo qué herramienta usar…</span>
          </div>
        ) : (
          <ol className="loop-steps">
            {steps.map((s) => (
              <li key={s.step}>
                <StepCard step={s} />
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
};

const useAnimatedPhase = (trace: TraceEntry[]): PhaseId | null => {
  const [phase, setPhase] = useState<PhaseId | null>(null);
  const queueRef = useRef<PhaseId[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSeenRef = useRef(0);

  useEffect(() => {
    // Reset when a new translation starts
    if (trace.length < lastSeenRef.current) {
      queueRef.current = [];
      lastSeenRef.current = 0;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      setPhase(null);
    }

    if (trace.length === lastSeenRef.current) return;

    // Translate new events into phase transitions
    for (let i = lastSeenRef.current; i < trace.length; i++) {
      const e = trace[i];
      const tail = queueRef.current[queueRef.current.length - 1];
      if (e.kind === 'start' || e.kind === 'thought') {
        if (tail !== 'think') queueRef.current.push('think');
      } else if (e.kind === 'action') {
        if (tail !== 'act') queueRef.current.push('act');
      } else if (e.kind === 'observation') {
        if (tail !== 'act') queueRef.current.push('act');
        queueRef.current.push('observe');
        queueRef.current.push('think');
      }
    }
    lastSeenRef.current = trace.length;

    // Start ticking if idle
    if (timerRef.current === null && queueRef.current.length > 0) {
      const tick = () => {
        const next = queueRef.current.shift();
        if (next === undefined) {
          timerRef.current = null;
          setPhase(null);
          return;
        }
        setPhase(next);
        timerRef.current = setTimeout(tick, MIN_DWELL_MS);
      };
      tick();
    }
  }, [trace.length]);

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  return phase;
};

const LoopDiagram = ({
  activePhase,
  iterations,
  done,
}: {
  activePhase: PhaseId | null;
  iterations: number;
  done: boolean;
}) => {
  const iterLabel = iterations === 1 ? 'iteración' : 'iteraciones';
  return (
    <div className={`loop-diagram ${done ? 'done' : ''}`}>
      <svg viewBox="0 0 280 184" className="loop-svg" role="img" aria-label="Bucle ReAct">
        <circle cx={RING_CX} cy={RING_CY} r={RING_RADIUS} className="loop-ring" />

        {ARROW_ANGLES.map((a) => (
          <ArrowOnRing key={a} angleDeg={a} />
        ))}

        {PHASES.map((p) => (
          <g key={p.id} className={`phase ${activePhase === p.id ? 'active' : ''}`}>
            <circle cx={p.x} cy={p.y} r="14" className="phase-node" />
            <text
              x={p.x}
              y={p.labelY}
              textAnchor="middle"
              dominantBaseline="central"
              className="phase-label"
            >
              {p.label}
            </text>
          </g>
        ))}

        <text
          x={RING_CX}
          y={RING_CY}
          textAnchor="middle"
          dominantBaseline="central"
          className="loop-iter-num"
        >
          {iterations}
        </text>
        <text
          x={RING_CX}
          y={RING_CY + 16}
          textAnchor="middle"
          dominantBaseline="central"
          className="loop-iter-label"
        >
          {iterLabel}
        </text>
      </svg>
      {done && <span className="loop-status-pill">completado</span>}
    </div>
  );
};

const ArrowOnRing = ({ angleDeg }: { angleDeg: number }) => {
  const rad = (angleDeg * Math.PI) / 180;
  const x = RING_CX + RING_RADIUS * Math.sin(rad);
  const y = RING_CY - RING_RADIUS * Math.cos(rad);
  return (
    <polygon
      className="loop-arrow"
      points="-5,-4 5,0 -5,4"
      transform={`translate(${x} ${y}) rotate(${angleDeg})`}
    />
  );
};

const STATUS_LABEL: Record<Step['status'], string> = {
  thinking: 'pensando',
  doing: 'esperando observación',
  done: 'listo',
};

const StepCard = ({ step }: { step: Step }) => (
  <div className={`loop-step ${step.status}`}>
    <div className="loop-step-header">
      <span className="loop-step-num">#{step.step}</span>
      <span className="loop-step-tool">
        <Icon name={step.icon} />
        <span>{step.tool || '—'}</span>
      </span>
      <span className={`loop-step-status ${step.status}`}>{STATUS_LABEL[step.status]}</span>
    </div>
    {step.thoughts.length > 0 && (
      <div className="loop-step-row">
        <span className="loop-step-row-label">thought</span>
        <div className="loop-step-row-value">
          {step.thoughts.map((t, i) => (
            <div key={i} className="loop-step-thought">{t}</div>
          ))}
        </div>
      </div>
    )}
    {step.warnings.map((w, i) => (
      <div key={`w-${i}`} className="loop-step-row loop-step-warning">
        <span className="loop-step-row-label">warning</span>
        <span className="loop-step-row-value">{w}</span>
      </div>
    ))}
    {step.tool && (
      <div className="loop-step-row">
        <span className="loop-step-row-label">input</span>
        <code className="loop-step-row-value code">{step.input}</code>
      </div>
    )}
    {step.observation !== undefined && (
      <div className="loop-step-row">
        <span className="loop-step-row-label">output</span>
        <span className="loop-step-row-value">{step.observation}</span>
      </div>
    )}
  </div>
);
