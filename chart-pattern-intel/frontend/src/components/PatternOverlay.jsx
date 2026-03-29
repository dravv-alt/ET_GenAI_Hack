// Overlays detected pattern markers on the chart
export default function PatternOverlay({ patterns = [] }) {
  return (
    <div className="card" style={{ display: 'grid', gap: 10 }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
        PATTERN OVERLAY
      </div>
      {patterns.length === 0 ? (
        <div style={{ color: 'var(--text-muted)' }}>No patterns to overlay.</div>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {patterns.slice(0, 6).map((pattern) => (
            <span key={pattern.pattern_type} className="pill">
              {pattern.pattern_type.replace('_', ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
