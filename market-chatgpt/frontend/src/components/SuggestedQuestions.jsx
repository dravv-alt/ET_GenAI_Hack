const QUESTION_TEMPLATES = [
  "Which pattern has the highest success rate in my portfolio?",
  "What is the average holding period for my bullish patterns?",
  "Are there any bearish divergence signals active on INFY?",
  "Show me all breakout patterns occurring today.",
  "Which tech stocks are showing bullish engulfing today?",
];

export function SuggestedQuestions({ onSelect }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 8, marginTop: 12 }}>
      {QUESTION_TEMPLATES.map((q, i) => (
        <button key={i} onClick={() => onSelect(q)}
          style={{
            textAlign: 'left',
            fontFamily: 'var(--sans)',
            fontSize: 12,
            color: 'var(--text-primary)',
            background: 'var(--bg-white)',
            border: '1px solid var(--border)',
            padding: '8px 12px',
            cursor: 'pointer',
            transition: 'background 0s, border-color 0s'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--bg-hover)';
            e.currentTarget.style.borderLeft = '2px solid var(--text-primary)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'var(--bg-white)';
            e.currentTarget.style.borderLeft = '1px solid var(--border)';
          }}
        >
          {q}
        </button>
      ))}
    </div>
  );
}
