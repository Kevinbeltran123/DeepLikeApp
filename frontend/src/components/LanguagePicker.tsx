import { useEffect, useRef, useState } from 'react';

interface Props {
  languages: Record<string, string>;
  value: string;
  onChange: (code: string) => void;
  includeAuto?: boolean;
  disabled?: boolean;
  label: string;
}

interface Option {
  code: string;
  name: string;
}

export const LanguagePicker = ({
  languages,
  value,
  onChange,
  includeAuto = false,
  disabled,
  label,
}: Props) => {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const options: Option[] = [
    ...(includeAuto ? [{ code: 'auto', name: 'Detectar idioma' }] : []),
    ...Object.entries(languages).map(([code, name]) => ({ code, name })),
  ];

  const current = options.find((o) => o.code === value);

  useEffect(() => {
    if (!open) return;
    const onMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const handleSelect = (code: string) => {
    onChange(code);
    setOpen(false);
  };

  return (
    <div
      className={`language-picker ${open ? 'open' : ''} ${disabled ? 'disabled' : ''}`}
      ref={containerRef}
    >
      <span className="language-picker-label">{label}</span>
      <button
        type="button"
        className="language-picker-trigger"
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="language-picker-current">{current?.name ?? value}</span>
        <span className="language-picker-chev" aria-hidden>▾</span>
      </button>

      {open && (
        <ul className="language-picker-menu" role="listbox">
          {options.map((o) => (
            <li
              key={o.code}
              role="option"
              aria-selected={o.code === value}
              className={`language-picker-option ${o.code === value ? 'selected' : ''}`}
              onClick={() => handleSelect(o.code)}
            >
              {o.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
