export function SourceChip({ source, number }) {
  return (
    <a 
      href={source.url} 
      target="_blank" 
      rel="noreferrer"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        textDecoration: 'none',
        background: 'var(--bg-white)',
        border: '1px solid var(--border)',
        padding: '2px 6px',
        fontFamily: 'var(--mono)',
        fontSize: 10,
        color: 'var(--text-secondary)',
        cursor: 'pointer',
        transition: 'background 0s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
      onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-white)'}
    >
      <span style={{ color: 'var(--text-muted)', marginRight: 4 }}>[{number}]</span>
      {source.title.length > 35 ? source.title.substring(0, 35) + '...' : source.title}
    </a>
  );
}
