import type { ModeId, ModeInfo } from '../types/events';

interface Props {
  modes: ModeInfo[];
  active: ModeId;
  onChange: (mode: ModeId) => void;
  disabled?: boolean;
}

export const ModeSelector = ({ modes, active, onChange, disabled }: Props) => (
  <div className="mode-selector" role="tablist">
    {modes.map((mode) => (
      <button
        key={mode.id}
        type="button"
        role="tab"
        aria-selected={mode.id === active}
        className={`mode-tab ${mode.id === active ? 'active' : ''}`}
        onClick={() => onChange(mode.id)}
        disabled={disabled}
        title={mode.description}
      >
        <span className="mode-tab-name">{mode.name}</span>
        <span className="mode-tab-desc">{mode.description}</span>
      </button>
    ))}
  </div>
);
