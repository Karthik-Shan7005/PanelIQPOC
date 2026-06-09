import MetricCards from './MetricCards';
import ResultTable from './ResultTable';
import ResultChart from './ResultChart';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'flex-end', marginBottom: '16px'
      }}>
        <div style={{
          background: '#1a2540', border: '1px solid #1e2a40',
          borderRadius: '12px 12px 3px 12px',
          padding: '10px 16px', maxWidth: '70%',
          fontSize: '13.5px', lineHeight: '1.6', color: '#e8edf5'
        }}>
          {message.content}
        </div>
      </div>
    );
  }

  // AI message
  const { content } = message;

  return (
    <div style={{
      display: 'flex', gap: '10px', marginBottom: '20px'
    }}>
      {/* Avatar */}
      <div style={{
        width: '30px', height: '30px', borderRadius: '8px',
        background: 'linear-gradient(135deg, #00d4ff, #7c6af7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '14px', flexShrink: 0, marginTop: '2px'
      }}>
        ⚡
      </div>

      <div style={{ flex: 1, maxWidth: 'calc(100% - 42px)' }}>

        {/* Loading state */}
        {content.loading && (
          <div style={{
            background: '#111928', border: '1px solid #1e2a40',
            borderRadius: '10px', padding: '12px 16px',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <div style={{ display: 'flex', gap: '4px' }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: '6px', height: '6px', borderRadius: '50%',
                  background: '#6b7a99',
                  animation: `bounce 1.2s infinite ${i * 0.2}s`
                }} />
              ))}
            </div>
            <span style={{ fontSize: '12px', color: '#6b7a99' }}>
              {content.loadingText || 'Analyzing your data...'}
            </span>
          </div>
        )}

        {/* Cancelled state */}
        {content.cancelled && !content.loading && (
          <div style={{
            background: '#1a1a24', border: '1px solid #3a3a5a',
            borderRadius: '10px', padding: '10px 16px',
            fontSize: '12px', color: '#6b7a99',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <span style={{ fontSize: '14px' }}>■</span>
            Analysis stopped. Type a new question below.
          </div>
        )}

        {/* Error state */}
        {content.error && !content.loading && (
          <div style={{
            background: '#2a1010', border: '1px solid #ff6b6b44',
            borderRadius: '10px', padding: '12px 16px',
            fontSize: '13px', color: '#ff6b6b'
          }}>
            ⚠️ {content.error}
          </div>
        )}

        {/* SQL chip */}
        {content.sql && !content.loading && (
          <div style={{
            background: '#0d1220', border: '1px solid #1e2a40',
            borderRadius: '8px', padding: '10px 14px',
            fontFamily: 'monospace', fontSize: '11px',
            color: '#7ca8e0', marginBottom: '8px',
            whiteSpace: 'pre-wrap', overflowX: 'auto'
          }}>
            <div style={{
              fontSize: '9px', color: '#6b7a99',
              letterSpacing: '1px', marginBottom: '6px',
              textTransform: 'uppercase'
            }}>
              Generated SQL
            </div>
            {content.sql}
          </div>
        )}

        {/* Metric cards for single row results */}
        {content.chartType === 'metric_cards' && !content.loading && (
          <MetricCards columns={content.columns} rows={content.rows} />
        )}

        {/* Chart */}
        {content.chartType !== 'metric_cards' && !content.loading && content.rows?.length > 0 && (
          <ResultChart
            chartType={content.chartType}
            columns={content.columns}
            rows={content.rows}
          />
        )}

        {/* Table */}
        {!content.loading && content.rows?.length > 0 && (
          <ResultTable
            columns={content.columns}
            rows={content.rows}
            rowCount={content.rowCount}
          />
        )}

        {/* Summary */}
        {content.summary && !content.loading && (
          <div style={{
            background: 'linear-gradient(135deg, #0d1a2e, #0d1525)',
            border: '1px solid #1a2d4a',
            borderRadius: '10px', padding: '12px 16px',
            fontSize: '13px', lineHeight: '1.75',
            color: '#b8c8e0', marginTop: '8px'
          }}>
            <span style={{ color: '#00e5a0', marginRight: '6px' }}>💡</span>
            <span dangerouslySetInnerHTML={{ __html: content.summary }} />
          </div>
        )}

        {/* Follow-up suggestion */}
        {content.followup && !content.loading && (
          <div style={{
            marginTop: '8px', fontSize: '12px', color: '#6b7a99',
            fontStyle: 'italic'
          }}>
            <span style={{ color: '#7c6af7' }}>💬 Suggested: </span>
            {content.followup}
          </div>
        )}

      </div>
    </div>
  );
}

// Add bounce animation to document
const style = document.createElement('style');
style.textContent = `
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-5px); opacity: 1; }
  }
`;
document.head.appendChild(style);