

// Displays support/resistance level badges
export default function LevelMarkers({ levels = [], formatPrice }) {
  if (!levels.length) {
    return (
      <div className="card">
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          KEY LEVELS
        </div>
        <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>No levels detected.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
        KEY LEVELS
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        {levels.map((level, idx) => (
          <span key={`${level.level_type}-${idx}`} className="pill">
            {level.level_type.toUpperCase()} {formatPrice ? formatPrice(level.price) : level.price.toFixed(2)}
          </span>
        ))}
      </div>
    </div>
  );
}
