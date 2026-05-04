interface Props {
  languages: Record<string, string>;
  value: string;
  onChange: (code: string) => void;
  includeAuto?: boolean;
  disabled?: boolean;
  label: string;
}

export const LanguagePicker = ({
  languages,
  value,
  onChange,
  includeAuto = false,
  disabled,
  label,
}: Props) => (
  <label className="language-picker">
    <span className="language-picker-label">{label}</span>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    >
      {includeAuto && <option value="auto">Detectar idioma</option>}
      {Object.entries(languages).map(([code, name]) => (
        <option key={code} value={code}>
          {name}
        </option>
      ))}
    </select>
  </label>
);
