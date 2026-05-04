import type { ModeId, ModeInfo } from '../types/events';

interface Props {
  modes: ModeInfo[];
  active: ModeId;
  onChange: (mode: ModeId) => void;
  disabled?: boolean;
}

export const ModeSelector = ({ modes, active, onChange, disabled }: Props) => {
  const activeMode = modes.find((m) => m.id === active);

  return (
    <div className="mode-selector">
      <div className="mode-pills" role="tablist">
        {modes.map((mode) => (
          <button
            key={mode.id}
            type="button"
            role="tab"
            aria-selected={mode.id === active}
            className={`mode-pill ${mode.id === active ? 'active' : ''}`}
            onClick={() => onChange(mode.id)}
            disabled={disabled}
          >
            {mode.name}
          </button>
        ))}
      </div>
      {activeMode && <p className="mode-description">{activeMode.description}</p>}
    </div>
  );
};
