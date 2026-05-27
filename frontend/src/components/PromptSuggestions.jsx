export default function PromptSuggestions({ suggestions, onSelect }) {
    if (!suggestions || suggestions.length === 0) return null;
  
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', gap: '4px',
        padding: '8px 0'
      }}>
        {suggestions.map((s, i) => (
          <div key={i}
            onClick={() => onSelect(s)}
            style={{
              padding: '8px 12px',
              background: '#111520',
              border: '1px solid #1e2a40',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#8a9bc0',
              cursor: 'pointer',
              transition: 'all 0.15s',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = '#00d4ff';
              e.currentTarget.style.color = '#e8edf5';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = '#1e2a40';
              e.currentTarget.style.color = '#8a9bc0';
            }}
          >
            <span style={{ color: '#00d4ff', fontSize: '10px' }}>→</span>
            {s}
          </div>
        ))}
      </div>
    );
  }