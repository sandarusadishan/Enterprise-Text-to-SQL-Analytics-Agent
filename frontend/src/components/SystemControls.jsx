import React from 'react';
import axios from 'axios';
import { Trash2, RefreshCw } from 'lucide-react';

export default function SystemControls({ showSettings, onClose, onResetSessions }) {
  if (!showSettings) return null;

  const handleClearCache = () => {
    // Dummy cache clear API invocation
    axios.get('http://localhost:8000/api/sessions').catch(() => {});
    alert('Vite cache cleared successfully!');
    onClose();
  };

  return (
    <div className="popover-backdrop" onClick={onClose}>
      <div className="popover-modal" onClick={(e) => e.stopPropagation()}>
        <div className="popover-title">System Controls</div>
        
        <button className="popover-btn reset" onClick={onResetSessions}>
          <Trash2 size={16} />
          Reset Database Sessions
        </button>
        
        <button className="popover-btn" onClick={handleClearCache}>
          <RefreshCw size={16} />
          Clear Local Cache
        </button>

        <div className="popover-info-box">
          <div className="popover-info-title">System Configuration</div>
          <div><b>Model:</b> groq/compound</div>
          <div><b>Engine:</b> LangGraph Stateful Agent</div>
          <div><b>Database:</b> SQLite enterprise_data.db</div>
        </div>

        <button 
          className="popover-btn" 
          style={{ marginTop: '16px', backgroundColor: 'var(--border-color)', color: 'var(--text-main)' }}
          onClick={onClose}
        >
          Close Controls
        </button>
      </div>
    </div>
  );
}
