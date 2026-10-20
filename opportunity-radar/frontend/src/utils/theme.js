// src/utils/theme.js

// Given pattern_type/alert_type / signal
export const signalColor = (type) =>
  type === 'bullish' || type === 'high' ? 'var(--green)' :
  type === 'bearish' || type === 'low'  ? 'var(--red)'   : 'var(--amber)'

export const signalBg = (type) =>
  type === 'bullish' || type === 'high' ? 'var(--green-bg)' :
  type === 'bearish' || type === 'low'  ? 'var(--red-bg)'   : 'var(--amber-bg)'

export const scoreColor = (score) =>
  score >= 80 ? 'var(--green)' :
  score >= 60 ? 'var(--amber)' : 'var(--red)'

// Helper to determine if an alert type is bullish, bearish, or neutral
export const getDirection = (alertType) => {
  const t = (alertType || '').toLowerCase()
  if (t.includes('buy') || t.includes('beat') || t.includes('approval') || t.includes('bullish')) return 'bullish'
  if (t.includes('sell') || t.includes('miss') || t.includes('bearish')) return 'bearish'
  return 'neutral'
}
