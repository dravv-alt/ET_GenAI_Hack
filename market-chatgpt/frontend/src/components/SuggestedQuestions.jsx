import { useState, useEffect } from 'react';

const QUESTION_TEMPLATES = [
  "Which pattern has the highest success rate in my portfolio?",
  "What is the average holding period for my bullish patterns?",
  "Are there any bearish divergence signals active on INFY?",
  "Show me all breakout patterns occurring today.",
  "Which tech stocks are showing bullish engulfing today?",
];

export function SuggestedQuestions({ portfolio, onSelect }) {
  const [questions, setQuestions] = useState(QUESTION_TEMPLATES);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!portfolio || portfolio.length === 0) {
      setQuestions(QUESTION_TEMPLATES);
      return;
    }
    
    let active = true;
    const fetchQ = async () => {
      setLoading(true);
      try {
        const res = await fetch('http://localhost:8003/portfolio/questions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tickers: portfolio.map(h => h.ticker) })
        });
        const data = await res.json();
        if (active && data.questions) setQuestions(data.questions);
      } catch (e) {
        console.error(e);
      }
      if (active) setLoading(false);
    };
    fetchQ();
    return () => { active = false; };
  }, [portfolio]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 8, marginTop: 12 }}>
      {loading && <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text-muted)' }}>GENERATING PORTFOLIO QUESTIONS...</div>}
      {!loading && questions.map((q, i) => (
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
