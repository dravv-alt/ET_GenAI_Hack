const BEARISH_TYPES = ['double_top', 'head_shoulders'];

function getScoreLabel(score) {
  if (score == null) return 'NO SIGNAL';
  if (score >= 85) return 'ELITE';
  if (score >= 70) return 'STRONG';
  if (score >= 55) return 'MODERATE';
  return 'WEAK';
}

function scoreColor(score) {
  if (score == null) return 'var(--text-muted)';
  if (score >= 85) return 'var(--green)';
  if (score >= 70) return 'var(--amber)';
  if (score >= 55) return 'var(--amber)';
  return 'var(--red)';
}

export default function ScorePanel({ patterns = [], selected, backtest }) {
  const pattern = selected || patterns[0];
  const confidence = pattern?.confidence ?? null;
  const recency = pattern?.recency ?? null;
  const winRate = backtest?.win_rate ?? null;
  const rankScore = typeof pattern?.key_levels?.rank_score === 'number' ? pattern.key_levels.rank_score : null;

  const curve = (value) => Math.pow(Math.max(Math.min(value, 1), 0), 1.7);
  let weighted = 0;
  let totalWeight = 0;
  if (confidence != null) {
    weighted += curve(confidence) * 0.45;
    totalWeight += 0.45;
  }
  if (recency != null) {
    weighted += curve(recency) * 0.25;
    totalWeight += 0.25;
  }
  if (winRate != null) {
    weighted += curve(winRate) * 0.2;
    totalWeight += 0.2;
  }
  if (rankScore != null) {
    weighted += curve(rankScore) * 0.1;
    totalWeight += 0.1;
  }
  let score = totalWeight ? Math.round((weighted / totalWeight) * 100) : null;
  const sampleCount = backtest?.sample_count ?? null;
  if (score != null && sampleCount != null) {
    if (sampleCount < 3) score = Math.round(score * 0.8);
    else if (sampleCount < 5) score = Math.round(score * 0.9);
  }
  const label = getScoreLabel(score);
  const isBearish = pattern ? BEARISH_TYPES.includes(pattern.pattern_type) : false;

  return (
    <div className="card" style={{ display: 'grid', gap: 12 }}>
      <div>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          SIGNAL SCORE
        </div>
        <div className="score-row">
          <div className="score-value" style={{ color: scoreColor(score) }}>
            {score ?? '—'}
          </div>
          <div className="score-label" style={{ color: scoreColor(score) }}>
            {label}
          </div>
        </div>
      </div>
      <div className="score-breakdown">
        <div>
          <div className="label">CONFIDENCE</div>
          <div className="value">{confidence != null ? `${(confidence * 100).toFixed(1)}%` : '—'}</div>
        </div>
        <div>
          <div className="label">RECENCY</div>
          <div className="value">{recency != null ? recency.toFixed(2) : '—'}</div>
        </div>
        <div>
          <div className="label">WIN RATE</div>
          <div className="value">{winRate != null ? `${(winRate * 100).toFixed(1)}%` : '—'}</div>
        </div>
      </div>
      <div>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          TOP PATTERN
        </div>
        {pattern ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
            <div style={{ fontWeight: 600 }}>{pattern.pattern_type.replace('_', ' ')}</div>
            <span className={`pill ${isBearish ? 'pill-negative' : 'pill-positive'}`}>
              {isBearish ? 'BEARISH' : 'BULLISH'}
            </span>
          </div>
        ) : (
          <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>No patterns detected.</div>
        )}
      </div>
    </div>
  );
}
