const MAX_LENGTH = 5000;

interface Props {
  text: string;
  onChange: (text: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isStreaming: boolean;
}

export const SourcePanel = ({ text, onChange, onSubmit, onCancel, isStreaming }: Props) => {
  const canSubmit = text.trim().length > 0 && !isStreaming;
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && canSubmit) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="panel source-panel">
      <textarea
        value={text}
        onChange={(e) => onChange(e.target.value.slice(0, MAX_LENGTH))}
        onKeyDown={handleKeyDown}
        placeholder="Escribe o pega el texto aqui..."
        disabled={isStreaming}
        spellCheck
      />
      <div className="panel-footer">
        <span className="char-count">{text.length} / {MAX_LENGTH}</span>
        {isStreaming ? (
          <button type="button" onClick={onCancel} className="btn btn-secondary">
            Cancelar
          </button>
        ) : (
          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSubmit}
            className="btn btn-primary"
          >
            Traducir
          </button>
        )}
      </div>
    </div>
  );
};
