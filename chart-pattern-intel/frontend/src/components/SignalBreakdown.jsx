// Shows signal explainability breakdown
export default function SignalBreakdown({ ensemble }) {
  if (!ensemble) {
    return (
      <div className="card">
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          WHY THIS SIGNAL
        </div>
        <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>No breakdown available.</div>
      </div>
    );
  }

  const patternFactors = ensemble.pattern_factors || [];
  const indicatorFactors = ensemble.indicator_factors || [];

  return (
    <div className="card" style={{ display: 'grid', gap: 10 }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
        WHY THIS SIGNAL
      </div>
      <div className="signal-breakdown">
        {patternFactors.map((item, idx) => (
          <div key={`pattern-${idx}`} className="signal-row signal-stack">
            <div className="signal-label">PATTERN</div>
            <div className="signal-value">{item.feature}</div>
            <div className="signal-score">{item.score.toFixed(1)}</div>
          </div>
        ))}
        {indicatorFactors.map((item, idx) => (
          <div key={`indicator-${idx}`} className="signal-row signal-stack">
            <div className="signal-label">INDICATOR</div>
            <div className="signal-value">{item.feature}</div>
            <div className="signal-score">{item.score.toFixed(1)}</div>
          </div>
        ))}
      </div>
      <div className="signal-row signal-total signal-stack">
        <div className="signal-label">ENSEMBLE</div>
        <div className="signal-value">{ensemble.direction}</div>
        <div className="signal-score">{ensemble.score.toFixed(2)}</div>
      </div>
    </div>
  );
}
