import { SignalCard } from './SignalCard';
import { SourceChip } from './SourceChip';

export function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="animate-in" style={{
        marginBottom: 16,
        padding: '10px 14px',
        background: '#fff',
        border: '1px solid var(--border)',
        borderLeft: '2px solid #555',
        alignSelf: 'flex-start',
        maxWidth: '85%'
      }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 4 }}>
          OPERATOR
        </div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-primary)' }}>
          {message.content}
        </div>
      </div>
    );
  }

  // Formatting heuristic: simple markdown bolding -> css for now
  const formatText = (txt) => {
      if(!txt) return "";
      let lines = txt.split('\n');
      return lines.map((line, i) => (
          <span key={i}>
              {line.replace(/\*\*(.*?)\*\*/g, "$1")}
              {i < lines.length - 1 && <br/>}
          </span>
      ));
  };

  return (
    <div className="animate-in" style={{
      marginBottom: 24,
      background: 'var(--bg-zebra)',
      border: '1px solid var(--border)',
      borderLeft: '2px solid var(--green)',
      width: '100%'
    }}>
      <div style={{
        padding: '6px 12px',
        background: '#f0f0f0',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em' }}>
          SYSTEM OUTPUT
        </span>
        {message.thinking && (
          <span className="pulse" style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--green)' }}>
            [ {message.thinking.toUpperCase()} ]
          </span>
        )}
      </div>

      <div style={{ padding: '14px' }}>
        <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: (message.signals?.length || message.sources?.length) ? 16 : 0 }}>
          {formatText(message.content)}
        </div>

        {message.signals && message.signals.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: message.sources?.length ? 12 : 0 }}>
            {message.signals.map((s, idx) => (
              <SignalCard key={idx} signal={s} />
            ))}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>REF:</span>
            {message.sources.map((src, idx) => (
              <SourceChip key={idx} source={src} number={idx + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
