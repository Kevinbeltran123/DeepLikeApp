import { useEffect, useMemo, useState } from 'react';

import { AgentTrace } from './components/AgentTrace';
import { LanguagePicker } from './components/LanguagePicker';
import { ModeSelector } from './components/ModeSelector';
import { SourcePanel } from './components/SourcePanel';
import { TranslationPanel } from './components/TranslationPanel';
import { useLanguages } from './hooks/useLanguages';
import { useTranslationStream } from './hooks/useTranslationStream';
import { fetchHealth, fetchModes } from './services/translationApi';
import type { HealthInfo } from './services/translationApi';
import type { ModeId, ModeInfo } from './types/events';

const App = () => {
  const { languages, loading: langsLoading } = useLanguages();
  const [modes, setModes] = useState<ModeInfo[]>([]);
  const [activeMode, setActiveMode] = useState<ModeId>('pipeline');
  const [health, setHealth] = useState<HealthInfo | null>(null);

  const [sourceText, setSourceText] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');

  const { state, translate, cancel, reset } = useTranslationStream();

  useEffect(() => {
    fetchModes().then(setModes).catch(() => setModes([]));
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const isStreaming = state.status === 'streaming';

  const activeModeInfo = useMemo(
    () => modes.find((m) => m.id === activeMode),
    [modes, activeMode],
  );

  const showTrace = activeModeInfo?.streams_steps ?? false;

  const handleSubmit = () => {
    reset();
    void translate(activeMode, {
      text: sourceText,
      source_lang: sourceLang,
      target_lang: targetLang,
    });
  };

  const handleSwap = () => {
    if (sourceLang === 'auto' || isStreaming) return;
    const newSource = targetLang;
    const newTarget = sourceLang;
    setSourceLang(newSource);
    setTargetLang(newTarget);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>
            DeepLikeApp
            {health && (
              <span
                className={`health-dot-inline ${health.ollama_reachable ? 'ok' : 'down'}`}
                title={
                  health.ollama_reachable
                    ? `Ollama conectado · ${health.model}`
                    : 'Ollama no disponible'
                }
                aria-label={health.ollama_reachable ? 'Backend conectado' : 'Backend no disponible'}
              />
            )}
          </h1>
          <p className="subtitle">
            Traductor estilo DeepL con tres arquitecturas comparables: pipeline, mono-agente y multi-agente.
          </p>
        </div>
      </header>

      <ModeSelector
        modes={modes}
        active={activeMode}
        onChange={setActiveMode}
        disabled={isStreaming}
      />

      <section className="translator">
        <div className="translator-controls">
          <LanguagePicker
            languages={languages}
            value={sourceLang}
            onChange={setSourceLang}
            includeAuto
            disabled={isStreaming || langsLoading}
            label="Origen"
          />
          <button
            type="button"
            className="swap-button"
            onClick={handleSwap}
            disabled={isStreaming || sourceLang === 'auto'}
            title={sourceLang === 'auto' ? 'No se puede invertir con deteccion automatica' : 'Invertir idiomas'}
            aria-label="Invertir idiomas"
          >
            &#8644;
          </button>
          <LanguagePicker
            languages={languages}
            value={targetLang}
            onChange={setTargetLang}
            disabled={isStreaming || langsLoading}
            label="Destino"
          />
        </div>

        <div className="translator-grid">
          <SourcePanel
            text={sourceText}
            onChange={setSourceText}
            onSubmit={handleSubmit}
            onCancel={cancel}
            isStreaming={isStreaming}
          />
          <TranslationPanel
            translation={state.translation}
            detectedLang={state.detectedLang}
            isStreaming={isStreaming}
            status={state.status}
          />
        </div>

        {state.status === 'error' && state.error && (
          <div className="error-banner">{state.error}</div>
        )}
      </section>

      {showTrace && (
        <section className="trace-section">
          <h2>
            {activeMode === 'monoagent' ? 'Bucle de razonamiento ReAct' : 'Pasos del orquestador'}
          </h2>
          <AgentTrace
            trace={state.trace}
            variant={activeMode === 'monoagent' ? 'monoagent' : 'multiagent'}
            status={state.status}
          />
        </section>
      )}

      <footer className="app-footer">
        <span>
          Backend: FastAPI + Ollama
          {health && ` · ${health.ollama_reachable ? 'conectado' : 'offline'}`}
        </span>
        <span>Modelo: {health?.model ?? 'qwen2.5:14b'}</span>
        <span>Cmd/Ctrl + Enter para traducir</span>
      </footer>
    </div>
  );
};

export default App;
