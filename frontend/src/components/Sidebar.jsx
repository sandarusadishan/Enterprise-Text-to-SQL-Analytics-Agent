import React from 'react';
import { Menu, Plus, Search, Sun, Moon, Settings, Pin, PinOff, Trash2, AlertCircle } from 'lucide-react';

export default function Sidebar({
  sidebarCollapsed,
  setSidebarCollapsed,
  onCreateSession,
  searchQuery,
  setSearchQuery,
  filteredSessions,
  activeSessionId,
  setActiveSessionId,
  theme,
  onToggleTheme,
  onShowSettings,
  pinnedSessionIds = [],
  onTogglePin,
  onDeleteSession,
  isBackendOffline
}) {
  const pinnedSessions = filteredSessions.filter(s => pinnedSessionIds.includes(s.session_id));
  const recentSessions = filteredSessions.filter(s => !pinnedSessionIds.includes(s.session_id));

  const renderSessionItem = (s, isPinned) => {
    return (
      <div
        key={s.session_id}
        className={`history-item-row ${activeSessionId === s.session_id ? 'active' : ''}`}
        onClick={() => setActiveSessionId(s.session_id)}
      >
        <div className="history-select-btn" title={s.session_name}>
          <span className="history-emoji">{isPinned ? '📌' : '💬'}</span>
          {!sidebarCollapsed && <span className="history-text">{s.session_name}</span>}
        </div>
        
        {!sidebarCollapsed && (
          <div className="history-actions">
            <button 
              className={`action-btn pin-btn ${isPinned ? 'pinned' : ''}`} 
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin(s.session_id);
              }}
              title={isPinned ? "Unpin session" : "Pin session"}
            >
              {isPinned ? <PinOff size={12} /> : <Pin size={12} />}
            </button>
            <button 
              className="action-btn delete-btn" 
              onClick={(e) => {
                e.stopPropagation();
                onDeleteSession(s.session_id, e);
              }}
              title="Delete session"
            >
              <Trash2 size={12} />
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      
      {/* Sidebar Top */}
      <div className="sidebar-top">
        <div className="sidebar-header">
          {!sidebarCollapsed && (
            <span className="brand-title">
              <img src="/logo.png" alt="Logo" style={{ width: '28px', height: '28px', borderRadius: '6px', objectFit: 'contain' }} />
              OmniQuery<span className="brand-dot"></span>
            </span>
          )}
          <button
            className="toggle-sidebar-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            style={{ position: 'relative' }}
          >
            <Menu size={20} />
            {isBackendOffline && sidebarCollapsed && (
              <span className="offline-pulse-dot" title="Server offline!" />
            )}
          </button>
        </div>

        <button className="new-chat-btn" onClick={onCreateSession}>
          <Plus size={18} />
          {!sidebarCollapsed && <span>New Analysis</span>}
        </button>

        {isBackendOffline && !sidebarCollapsed && (
          <div className="offline-banner">
            <AlertCircle size={14} className="offline-icon" />
            <span>Server offline. Run python main.py</span>
          </div>
        )}

        {!sidebarCollapsed && (
          <div className="sidebar-search-box">
            <Search className="sidebar-search-icon" size={15} />
            <input
              type="text"
              className="sidebar-search-input"
              placeholder="Search analyses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Scrollable chat thread history */}
      <div className="sidebar-history">
        {/* Pinned Sessions Section */}
        {pinnedSessions.length > 0 && !sidebarCollapsed && (
          <div className="sidebar-section-title">Pinned Sessions</div>
        )}
        {pinnedSessions.map(s => renderSessionItem(s, true))}

        {/* Recent Sessions Section */}
        {recentSessions.length > 0 && !sidebarCollapsed && (
          <div className="sidebar-section-title">Recent Sessions</div>
        )}
        {recentSessions.map(s => renderSessionItem(s, false))}
      </div>

      {/* Sidebar Profile Card Footer */}
      <div className="sidebar-footer">
        <div className="profile-card">
          <div className="avatar">SS</div>
          {!sidebarCollapsed && (
            <div className="profile-info">
              <span className="profile-name">S.Sadishan</span>
              <span className="profile-plan">Enterprise AI Pro</span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <button
            className="settings-trigger"
            onClick={onToggleTheme}
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {!sidebarCollapsed && (
            <button
              className="settings-trigger"
              onClick={onShowSettings}
              title="System Controls"
            >
              <Settings size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
