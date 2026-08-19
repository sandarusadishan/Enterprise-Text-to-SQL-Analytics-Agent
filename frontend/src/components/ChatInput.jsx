import React from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({ inputText, setInputText, onSendMessage, loading }) {
  return (
    <div className="chat-input-container">
      <form onSubmit={onSendMessage} className="chat-input-bar">
        <input 
          type="text" 
          className="chat-text-input" 
          placeholder="Ask a question about your business data..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={loading}
        />
        <button 
          type="submit" 
          className="send-btn" 
          disabled={loading || !inputText.trim()}
          title="Submit analysis query"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
