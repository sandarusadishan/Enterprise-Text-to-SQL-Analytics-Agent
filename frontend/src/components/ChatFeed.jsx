import React, { useState } from 'react';
import { Terminal, ChevronUp, ChevronDown, Sparkles, Copy, Check } from 'lucide-react';
import VisualizationComponents from './VisualizationComponents';

export default function ChatFeed({ messages, loading, expandedSql, onToggleSql, handleExportCSV, theme, onSelectQuickQuery, chatEndRef }) {
  const [copiedId, setCopiedId] = useState(null);

  const handleCopySql = (sqlText, idx) => {
    navigator.clipboard.writeText(sqlText);
    setCopiedId(idx);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const quickQueries = [
    {
      title: "💰 Total Revenue",
      query: "What is the total sales amount?",
      desc: "Calculate cumulative sales earnings across all categories."
    },
    {
      title: "🔥 Top Customer",
      query: "Which customer purchased the most in electronics?",
      desc: "Retrieve details of the highest spending customer."
    },
    {
      title: "📈 Product Profits",
      query: "wadiyenma sale wenne mona itemsda charts ekkama profit ekath ekka danna?",
      desc: "Show highest selling products and analyze profit margins."
    },
    {
      title: "📊 Category Overview",
      query: "Show sales distribution and details by product categories.",
      desc: "Get group-wise categories metrics breakdown."
    }
  ];

  return (
    <div className="chat-feed">
      {messages.length === 0 ? (
        <div className="chat-welcome-container">
          <div className="welcome-glow-dot"></div>
          <div className="welcome-badge">
            <Sparkles size={14} className="welcome-badge-icon" />
            <span>Autonomous BI Analytics Engine</span>
          </div>
          <h2 className="welcome-title">Ask OmniQuery Anything</h2>
          <p className="welcome-subtitle">
            Enter complex business intelligence questions. The agent will write SQLite queries, execute them, correct syntax, and render visualizations.
          </p>
          
          <div className="quick-queries-grid">
            {quickQueries.map((item, idx) => (
              <div 
                key={idx} 
                className="quick-query-card"
                onClick={() => onSelectQuickQuery(item.query)}
              >
                <div className="quick-query-card-title">{item.title}</div>
                <div className="quick-query-card-desc">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div key={msg.id || idx} className={`message-row ${isUser ? 'user' : 'assistant'}`}>
              {!isUser && <div className="message-avatar assistant">AI</div>}
              
              <div className="message-bubble">
                {isUser ? (
                  <p className="markdown-paragraph">{msg.content}</p>
                ) : (
                  renderMarkdown(msg.content)
                )}

                {/* SQL query card (collapsible expander) */}
                {!isUser && msg.sql_query && (
                  <div className="sql-expander">
                    <div 
                      className="sql-expander-header" 
                      onClick={() => onToggleSql(idx)}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Terminal size={14} style={{ color: 'var(--accent-cyan)' }} />
                        Executed SQL Query
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button 
                          className="copy-sql-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopySql(msg.sql_query, idx);
                          }}
                          title="Copy SQL Query"
                        >
                          {copiedId === idx ? <Check size={13} style={{ color: 'var(--accent-green)' }} /> : <Copy size={13} />}
                        </button>
                        {expandedSql[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </span>
                    </div>
                    {expandedSql[idx] && (
                      <pre className="sql-expander-content"><code>{msg.sql_query}</code></pre>
                    )}
                  </div>
                )}

                {/* Metrics and Visualization Tabs */}
                {!isUser && msg.query_result_json && (
                  <VisualizationComponents 
                    resultJson={msg.query_result_json}
                    sql={msg.sql_query}
                    question={messages[Math.max(0, idx - 1)]?.content || 'Business Question'}
                    onExportCSV={handleExportCSV}
                    theme={theme}
                  />
                )}
              </div>
              
              {isUser && <div className="message-avatar user">SS</div>}
            </div>
          );
        })
      )}

      {loading && (
        <div className="loader-container">
          <div className="spinner"></div>
          <span>Thinking, writing SQL, and retrieving results...</span>
        </div>
      )}

      <div ref={chatEndRef} />
    </div>
  );
}

// Lightweight senior-grade markdown rendering utility functions to format list items and bold tags cleanly
function renderMarkdown(text) {
  if (!text) return null;
  
  const lines = text.split('\n');
  const renderedElements = [];
  let currentList = [];
  
  lines.forEach((line, idx) => {
    // Check if it's a list item starting with "- " or "* "
    const listMatch = line.match(/^[\s]*[-*]\s+(.*)$/);
    if (listMatch) {
      const content = listMatch[1];
      currentList.push(
        <li key={`li-${idx}`}>
          {parseInlineMarkdown(content)}
        </li>
      );
    } else {
      // If we had a list building up, render it first
      if (currentList.length > 0) {
        renderedElements.push(
          <ul key={`ul-${idx}`} className="markdown-list">
            {currentList}
          </ul>
        );
        currentList = [];
      }
      
      // Render line spacing or paragraph
      if (line.trim() === '') {
        renderedElements.push(<div key={`space-${idx}`} className="markdown-space" />);
      } else {
        renderedElements.push(
          <p key={`p-${idx}`} className="markdown-paragraph">
            {parseInlineMarkdown(line)}
          </p>
        );
      }
    }
  });
  
  if (currentList.length > 0) {
    renderedElements.push(
      <ul key="ul-final" className="markdown-list">
        {currentList}
      </ul>
    );
  }
  
  return <div className="markdown-container">{renderedElements}</div>;
}

function parseInlineMarkdown(content) {
  if (!content) return '';
  const parts = content.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      const cleanPart = part.slice(2, -2);
      return <strong key={index} style={{ fontWeight: '700' }}>{cleanPart}</strong>;
    }
    return part;
  });
}
