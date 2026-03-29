// Displays one detected pattern with entry/SL/target levels
export default function PatternCard({ pattern, active, onSelect }) {
  const bearishTypes = ['double_top', 'head_shoulders'];
  const isBearish = bearishTypes.includes(pattern.pattern_type);
  const direction = isBearish ? 'BEARISH' : 'BULLISH';
  const dirClass = isBearish ? 'pill-negative' : 'pill-positive';
  const rankScore = typeof pattern.key_levels?.rank_score === 'number' ? pattern.key_levels.rank_score : null;

  return (
    <button
      type="button"
      className={`pattern-card ${active ? 'active' : ''}`}
      onClick={() => onSelect?.(pattern)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
            PATTERN DETECTED
          </div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{pattern.pattern_type.replace('_', ' ')}</div>
        </div>
        <span className={`pill ${dirClass}`}>{direction}</span>
      </div>
      <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
        <div className="stat-row">
          <span className="label">CONF</span>
          <span className="value">{(pattern.confidence * 100).toFixed(1)}%</span>
        </div>
        <div className="stat-row">
          <span className="label">ENTRY</span>
          <span className="value">{pattern.entry_price.toFixed(2)}</span>
        </div>
        <div className="stat-row">
          <span className="label">STOP</span>
          <span className="value">{pattern.stop_loss.toFixed(2)}</span>
        </div>
        <div className="stat-row">
          <span className="label">TARGET</span>
          <span className="value">{pattern.target_price.toFixed(2)}</span>
        </div>
        {rankScore !== null && (
          <div className="stat-row">
            <span className="label">RANK</span>
            <span className="value">{rankScore.toFixed(2)}</span>
          </div>
        )}
      </div>
    </button>
  );
}
