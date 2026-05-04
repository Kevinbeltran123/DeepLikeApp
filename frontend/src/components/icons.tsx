// Inline SVG icons. Backend agents and tools reference these by string id
// (search, book, globe, check, robot, spark). Mapping lives here so the
// backend never depends on UI details.

import type { JSX, SVGProps } from 'react';

const base: SVGProps<SVGSVGElement> = {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export const SearchIcon = () => (
  <svg {...base}>
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

export const BookIcon = () => (
  <svg {...base}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
  </svg>
);

export const GlobeIcon = () => (
  <svg {...base}>
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

export const CheckIcon = () => (
  <svg {...base}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export const RobotIcon = () => (
  <svg {...base}>
    <rect x="4" y="8" width="16" height="12" rx="2" />
    <line x1="12" y1="3" x2="12" y2="8" />
    <circle cx="9" cy="14" r="1" />
    <circle cx="15" cy="14" r="1" />
  </svg>
);

export const SparkIcon = () => (
  <svg {...base}>
    <polygon points="12 2 14 9 22 12 14 15 12 22 10 15 2 12 10 9 12 2" />
  </svg>
);

const ICON_MAP: Record<string, () => JSX.Element> = {
  search: SearchIcon,
  book: BookIcon,
  globe: GlobeIcon,
  check: CheckIcon,
  robot: RobotIcon,
  spark: SparkIcon,
};

export const Icon = ({ name }: { name: string }) => {
  const Component = ICON_MAP[name] ?? SparkIcon;
  return <Component />;
};
