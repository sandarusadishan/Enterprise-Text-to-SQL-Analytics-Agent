import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import ChatInput from './components/ChatInput';
import SystemControls from './components/SystemControls';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSql, setExpandedSql] = useState({});
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [isBackendOffline, setIsBackendOffline] = useState(false);
  const [pinnedSessionIds, setPinnedSessionIds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('pinnedSessions') || '[]');
    } catch {
      return [];
    }
  });
  
  const chatEndRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Fetch all chat session threads
  const fetchSessions = async (selectLatest = false) => {
    try {
      const res = await axios.get(`${API_BASE}/sessions`);
      setSessions(res.data);
      setIsBackendOffline(false);
      if (res.data.length > 0) {
        if (selectLatest || !activeSessionId) {
          setActiveSessionId(res.data[0].session_id);
        }
      } else {
        createSession();
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setIsBackendOffline(true);
    }
  };

  // Create a new chat session thread
  const createSession = async () => {
    try {
      const res = await axios.post(`${API_BASE}/sessions`);
      setActiveSessionId(res.data.session_id);
      setIsBackendOffline(false);
      fetchSessions(false);
    } catch (err) {
      console.error('Error creating session:', err);
      setIsBackendOffline(true);
    }
  };

  // Delete a chat session thread
  const handleDeleteSession = async (sessionId, e) => {
    if (e) e.stopPropagation();
    try {
      await axios.delete(`${API_BASE}/sessions/${sessionId}`);
      
      // Remove from pinned session ids if deleted
      setPinnedSessionIds(prev => {
        const next = prev.filter(id => id !== sessionId);
        localStorage.setItem('pinnedSessions', JSON.stringify(next));
        return next;
      });

      // Select next active session if the deleted one was active
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter(s => s.session_id !== sessionId);
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].session_id);
        } else {
          setActiveSessionId(null);
        }
      }
      fetchSessions(false);
    } catch (err) {
      console.error('Error deleting session:', err);
    }
  };

  // Toggle session pinned state
  const handleTogglePin = (sessionId) => {
    setPinnedSessionIds(prev => {
      const isPinned = prev.includes(sessionId);
      const next = isPinned 
        ? prev.filter(id => id !== sessionId) 
        : [...prev, sessionId];
      localStorage.setItem('pinnedSessions', JSON.stringify(next));
      return next;
    });
  };

  // Fetch messages for the active session
  const fetchMessages = async (sessionId) => {
    if (!sessionId) return;
    try {
      const res = await axios.get(`${API_BASE}/sessions/${sessionId}/messages`);
      setMessages(res.data);
      setIsBackendOffline(false);
    } catch (err) {
      console.error('Error fetching messages:', err);
      setIsBackendOffline(true);
    }
  };

  // Send a new prompt to the backend FastAPI server
  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || !activeSessionId || loading) return;

    const userText = inputText;
    setInputText('');
    setLoading(true);

    // Optimistically render user message
    setMessages(prev => [...prev, { role: 'user', content: userText }]);

    try {
      const res = await axios.post(`${API_BASE}/sessions/${activeSessionId}/messages`, {
        question: userText
      });
      // Append assistant response
      setMessages(prev => [...prev, res.data]);
      setIsBackendOffline(false);
      // Refresh sessions to update titles (if auto-renamed)
      fetchSessions(false);
    } catch (err) {
      console.error('Error sending message:', err);
      setIsBackendOffline(true);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '❌ Error: Failed to execute query. Make sure backend is running.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Reset all session threads
  const handleResetSession = async () => {
    try {
      for (const s of sessions) {
        await axios.delete(`${API_BASE}/sessions/${s.session_id}`);
      }
      setActiveSessionId(null);
      setPinnedSessionIds([]);
      localStorage.removeItem('pinnedSessions');
      fetchSessions(true);
      setShowSettings(false);
    } catch (err) {
      console.error('Error resetting database:', err);
    }
  };

  // Load list of sessions on component mount
  useEffect(() => {
    fetchSessions(true);
  }, []);

  // Fetch active session messages when the active session changes
  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // Auto scroll chat to the bottom when messages list changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const toggleSql = (msgId) => {
    setExpandedSql(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  // Export query results table as CSV
  const handleExportCSV = (question, sql, cols, rows) => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Enterprise Text-to-SQL Analytics Report\n\n";
    csvContent += `Question,${question}\n`;
    csvContent += `SQL,${sql}\n\n`;
    csvContent += cols.join(",") + "\n";
    rows.forEach(row => {
      csvContent += row.join(",") + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `analytics_report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filtered sessions for sidebar search
  const filteredSessions = sessions.filter(s => 
    s.session_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="app-container">
      
      {/* 1. Sidebar Section */}
      <Sidebar 
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        onCreateSession={createSession}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        filteredSessions={filteredSessions}
        activeSessionId={activeSessionId}
        setActiveSessionId={setActiveSessionId}
        theme={theme}
        onToggleTheme={toggleTheme}
        onShowSettings={() => setShowSettings(true)}
        pinnedSessionIds={pinnedSessionIds}
        onTogglePin={handleTogglePin}
        onDeleteSession={handleDeleteSession}
        isBackendOffline={isBackendOffline}
      />
      
      {/* 2. Main Chat Panel */}
      <div className="main-panel">
        
        {/* Main Header */}
        <div className="main-header">
          <div className="main-header-title">
            <span className="main-header-sub"></span> Autonomous BI Agent
          </div>
        </div>

        {/* Messages Feed Area */}
        <ChatFeed 
          messages={messages}
          loading={loading}
          expandedSql={expandedSql}
          onToggleSql={toggleSql}
          handleExportCSV={handleExportCSV}
          theme={theme}
          onSelectQuickQuery={(q) => setInputText(q)}
          chatEndRef={chatEndRef}
        />

        {/* Fixed Bottom Input Bar */}
        <ChatInput 
          inputText={inputText}
          setInputText={setInputText}
          onSendMessage={handleSendMessage}
          loading={loading}
        />
      </div>

      {/* 3. System Controls Popover Modal */}
      <SystemControls 
        showSettings={showSettings}
        onClose={() => setShowSettings(false)}
        onResetSessions={handleResetSession}
      />
    </div>
  );
}
