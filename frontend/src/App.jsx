import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { askQuestionStream, getSuggestions } from './api/paneliq';
import MessageBubble from './components/MessageBubble';
import PromptSuggestions from './components/PromptSuggestions';
import LogoPanelGrid from './components/LogoPanelGrid';

const SIDEBAR_QUESTIONS = [
  "Show me completes by market for last 6 months",
  "Give me invites, clicks and completes for March 2026",
  "What is the screenout breakdown by status group this year?",
  "Which markets have the highest incidence rate in Q1 2026?",
  "Compare monthly completes trend for last 12 months",
  "Show me internal TPS vs external completes by market",
  "Which projects are live right now?",
  "Give me overall panel health summary for this year",
  "What is the click rate and conversion rate by country?",
  "Show fraud and quality rejection rate by market",
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const suggestTimer = useRef(null);
  const abortControllerRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Debounced suggestions
  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);

    clearTimeout(suggestTimer.current);
    if (val.length >= 3) {
      suggestTimer.current = setTimeout(async () => {
        const s = await getSuggestions(val);
        setSuggestions(s);
        setShowSuggestions(s.length > 0);
      }, 600);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const sendMessage = async (question) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput('');
    setSuggestions([]);
    setShowSuggestions(false);
    setLoading(true);

    // Add user message
    const userMsg = { role: 'user', content: q, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);

    // Add loading AI message
    const aiId = Date.now() + 1;
    setMessages(prev => [...prev, {
      role: 'ai',
      id: aiId,
      content: {
        loading: true,
        loadingText: 'Generating SQL and querying database...'
      }
    }]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const update = (patch) =>
      setMessages(prev => prev.map(m =>
        m.id === aiId ? { ...m, content: { ...m.content, ...patch } } : m
      ));

    try {
      await askQuestionStream(q, (event) => {
        switch (event.type) {
          case 'sql_chunk':
            setMessages(prev => prev.map(m => {
              if (m.id !== aiId) return m;
              return { ...m, content: { ...m.content, loadingText: 'Generating SQL…', sql: (m.content.sql || '') + event.content } };
            }));
            break;
          case 'sql_done':
            update({ sql: event.content, loadingText: 'SQL ready — querying database…' });
            break;
          case 'status':
            update({ loadingText: event.content });
            break;
          case 'data':
            update({
              columns:  event.content.columns,
              rows:     event.content.rows,
              rowCount: event.content.row_count,
              loadingText: 'Analysing results…',
            });
            break;
          case 'summary_chunk':
            setMessages(prev => prev.map(m => {
              if (m.id !== aiId) return m;
              return { ...m, content: { ...m.content, summary: (m.content.summary || '') + event.content } };
            }));
            break;
          case 'summary_done':
            update({ summary: event.content.summary, followup: event.content.followup });
            break;
          case 'chart':
            update({ chartType: event.content });
            break;
          case 'error':
            update({ loading: false, error: event.content });
            break;
          case 'done':
            update({ loading: false });
            break;
        }
      }, controller.signal);

    } catch (err) {
      const cancelled = err?.name === 'AbortError';
      update({ loading: false, cancelled, error: cancelled ? null : (err?.message || 'Could not reach the backend.') });
    }

    abortControllerRef.current = null;
    setLoading(false);
    inputRef.current?.focus();
  };

  const stopAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      display: 'flex', height: '100vh',
      fontFamily: "'Segoe UI', sans-serif",
      background: '#0a0d14', color: '#e8edf5'
    }}>

      {/* SIDEBAR */}
      <div style={{
        width: '240px', background: '#111520',
        borderRight: '1px solid #1e2a40',
        display: 'flex', flexDirection: 'column',
        flexShrink: 0, overflowY: 'auto'
      }}>
        {/* Logo */}
        <div style={{
          padding: '18px 16px',
          borderBottom: '1px solid #1e2a40'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <LogoPanelGrid size={36} />
            <div>
              <div style={{
                fontWeight: '800', fontSize: '17px', letterSpacing: '-0.5px'
              }}>
                Panel-IQ
              </div>
              <div style={{ fontSize: '10px', color: '#6b7a99' }}>
                Panel Intelligence
              </div>
            </div>
          </div>
        </div>

        {/* Sample questions */}
        <div style={{ padding: '14px 0' }}>
          <div style={{
            fontSize: '9px', fontWeight: '700',
            letterSpacing: '1.5px', color: '#6b7a99',
            padding: '0 16px 8px',
            textTransform: 'uppercase'
          }}>
            Sample Questions
          </div>
          {SIDEBAR_QUESTIONS.map((q, i) => (
            <div key={i}
              onClick={() => sendMessage(q)}
              style={{
                padding: '8px 16px', fontSize: '12px',
                color: '#8a9bc0', cursor: 'pointer',
                borderLeft: '2px solid transparent',
                transition: 'all 0.15s', lineHeight: '1.5'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = '#161c2c';
                e.currentTarget.style.color = '#e8edf5';
                e.currentTarget.style.borderLeftColor = '#00d4ff';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = '#8a9bc0';
                e.currentTarget.style.borderLeftColor = 'transparent';
              }}
            >
              <span style={{ color: '#00d4ff', marginRight: '6px', fontSize: '10px' }}>→</span>
              {q}
            </div>
          ))}
        </div>

        {/* Module badge */}
        <div style={{
          marginTop: 'auto', padding: '14px 16px',
          borderTop: '1px solid #1e2a40'
        }}>
          <div style={{
            fontSize: '9px', color: '#6b7a99',
            textTransform: 'uppercase', letterSpacing: '1px',
            marginBottom: '6px'
          }}>
            Active Module
          </div>
          <div style={{
            fontSize: '11px', padding: '4px 10px',
            border: '1px solid #00e5a0',
            color: '#00e5a0', borderRadius: '20px',
            display: 'inline-block'
          }}>
            ● Engagement POC
          </div>
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div style={{
        flex: 1, display: 'flex',
        flexDirection: 'column', overflow: 'hidden'
      }}>

        {/* Header */}
        <div style={{
          padding: '12px 24px',
          borderBottom: '1px solid #1e2a40',
          background: '#111520',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', flexShrink: 0
        }}>
          <div style={{ fontSize: '13px', color: '#6b7a99' }}>
            Connected to <span style={{ color: '#00d4ff' }}>KpiReports</span> ·
            Model: <span style={{ color: '#7c6af7' }}>claude-sonnet-4-20250514</span>
          </div>
          <div style={{
            fontSize: '10px', padding: '3px 10px',
            border: '1px solid #00d4ff33',
            color: '#00d4ff', borderRadius: '20px',
            fontFamily: 'monospace'
          }}>
            ● LIVE
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1, overflowY: 'auto',
          padding: '24px', display: 'flex',
          flexDirection: 'column', gap: '4px'
        }}>

          {/* Welcome screen */}
          {messages.length === 0 && (
            <div style={{
              textAlign: 'center', padding: '40px 20px',
              maxWidth: '560px', margin: '0 auto'
            }}>
              <div style={{
                fontSize: '28px', fontWeight: '800',
                background: 'linear-gradient(90deg, #00d4ff, #7c6af7)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: '10px'
              }}>
                Ask your panel data anything.
              </div>
              <div style={{
                fontSize: '13px', color: '#6b7a99',
                lineHeight: '1.7', marginBottom: '20px'
              }}>
                Type a question in plain English. I'll query your
                KpiReports database and return metrics,
                charts and analyst insights instantly.
              </div>
              <div style={{
                display: 'flex', flexWrap: 'wrap',
                gap: '8px', justifyContent: 'center'
              }}>
                {['Invites', 'Clicks', 'Completes', 'IR%',
                  'Click Rate', 'Conv. Rate', 'Screenouts',
                  'Market Analysis'].map(tag => (
                  <span key={tag} style={{
                    fontSize: '11px', padding: '3px 10px',
                    border: '1px solid #1e2a40',
                    borderRadius: '20px', color: '#7c6af7'
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid #1e2a40',
          background: '#111520', flexShrink: 0
        }}>
          {/* Suggestions */}
          {showSuggestions && (
            <PromptSuggestions
              suggestions={suggestions}
              onSelect={(s) => {
                setInput(s);
                setShowSuggestions(false);
                inputRef.current?.focus();
              }}
            />
          )}

          {/* Input box */}
          <div style={{
            display: 'flex', gap: '10px', alignItems: 'flex-end',
            background: '#161c2c', border: '1px solid #1e2a40',
            borderRadius: '12px', padding: '10px 14px',
            transition: 'border-color 0.2s'
          }}
            onFocus={e => e.currentTarget.style.borderColor = '#00d4ff'}
            onBlur={e => e.currentTarget.style.borderColor = '#1e2a40'}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your panel data... e.g. Show completes by market for March 2026"
              rows={1}
              style={{
                flex: 1, background: 'none', border: 'none',
                outline: 'none', color: '#e8edf5',
                fontFamily: "'Segoe UI', sans-serif",
                fontSize: '13px', resize: 'none',
                maxHeight: '100px', lineHeight: '1.5'
              }}
              onInput={e => {
                e.target.style.height = 'auto';
                e.target.style.height =
                  Math.min(e.target.scrollHeight, 100) + 'px';
              }}
            />
            {loading ? (
              <button
                onClick={stopAnalysis}
                title="Stop analysis"
                style={{
                  background: '#2a1a1a',
                  border: '1px solid #ff4d4d55',
                  borderRadius: '8px',
                  width: '36px', height: '36px',
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center',
                  justifyContent: 'center', flexShrink: 0,
                  transition: 'all 0.2s', fontSize: '14px',
                  color: '#ff6b6b',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = '#3a1a1a';
                  e.currentTarget.style.borderColor = '#ff4d4d';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = '#2a1a1a';
                  e.currentTarget.style.borderColor = '#ff4d4d55';
                }}
              >
                ■
              </button>
            ) : (
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim()}
                style={{
                  background: !input.trim()
                    ? '#1e2a40'
                    : 'linear-gradient(135deg, #00d4ff, #7c6af7)',
                  border: 'none', borderRadius: '8px',
                  width: '36px', height: '36px',
                  cursor: !input.trim() ? 'default' : 'pointer',
                  display: 'flex', alignItems: 'center',
                  justifyContent: 'center', flexShrink: 0,
                  transition: 'all 0.2s', fontSize: '16px'
                }}
              >
                ➤
              </button>
            )}
          </div>
          <div style={{
            fontSize: '10px', color: '#6b7a99',
            textAlign: 'center', marginTop: '6px'
          }}>
            Powered by Claude AI · KPISurveyData + KPIReportProjectData ·
            Engagement Surveys excluded automatically
          </div>
        </div>
      </div>
    </div>
  );
}