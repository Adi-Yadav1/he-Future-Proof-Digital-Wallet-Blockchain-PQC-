/**
 * Phase 9 — Design tokens
 * Single source of truth for colors, typography, and spacing.
 * All screens import from here to stay visually consistent.
 */

export const colors = {
  bg: '#0f172a',        // deep navy — main background
  surface: '#1e293b',   // card / panel backgrounds
  surfaceAlt: '#243044',
  border: '#334155',
  inputBg: '#0f172a',
  accent: '#38bdf8',    // sky blue — primary CTA
  accentAlt: '#2dd4bf', // teal — secondary
  success: '#4ade80',
  error: '#f87171',
  warning: '#fbbf24',
  textPrimary: '#f1f5f9',
  textSecondary: '#cbd5e1',
  textMuted: '#64748b',
  encrypted: '#a78bfa', // purple for private/encrypted items
}

export const typography = {
  h1: { fontSize: 26, fontWeight: '800', letterSpacing: 0.3 },
  h2: { fontSize: 20, fontWeight: '700' },
  h3: { fontSize: 17, fontWeight: '600' },
  body: { fontSize: 15, fontWeight: '400', lineHeight: 22 },
  label: { fontSize: 13, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  caption: { fontSize: 12, fontWeight: '400' },
  mono: { fontSize: 13, fontFamily: 'monospace' },
}

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 40,
}

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
}
