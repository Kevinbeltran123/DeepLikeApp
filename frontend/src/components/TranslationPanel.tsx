interface Props {
  translation: string;
  detectedLang: { code: string; display: string } | null;
  isStreaming: boolean;
  status: 'idle' | 'streaming' | 'done' | 'error';
}

export const TranslationPanel = ({ translation, detectedLang, isStreaming, status }: Props) => (
  <div className="panel translation-panel">
    {detectedLang && (
      <div className="detected-lang">
        Origen detectado: <strong>{detectedLang.display}</strong>
      </div>
    )}
    <div className={`translation-output ${isStreaming ? 'streaming' : ''}`}>
      {translation || <span className="placeholder">La traduccion aparecera aqui...</span>}
      {isStreaming && <span className="cursor">|</span>}
    </div>
    <div className="panel-footer">
      <span className="status-pill" data-status={status}>
        {status === 'idle' && 'Listo'}
        {status === 'streaming' && 'Traduciendo...'}
        {status === 'done' && 'Completado'}
        {status === 'error' && 'Error'}
      </span>
    </div>
  </div>
);
