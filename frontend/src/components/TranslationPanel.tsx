interface Props {
  translation: string;
  detectedLang: { code: string; display: string } | null;
  isStreaming: boolean;
  status: 'idle' | 'streaming' | 'done' | 'error';
}

export const TranslationPanel = ({ translation, isStreaming }: Props) => (
  <div className="panel translation-panel">
    <div className={`translation-output ${isStreaming ? 'streaming' : ''}`}>
      {!translation && !isStreaming && (
        <span className="placeholder">La traducción aparecerá aquí…</span>
      )}
      {!translation && isStreaming && (
        <span className="translating">Traduciendo</span>
      )}
      {translation && (
        <>
          {translation}
          {isStreaming && <span className="cursor">|</span>}
        </>
      )}
    </div>
  </div>
);
