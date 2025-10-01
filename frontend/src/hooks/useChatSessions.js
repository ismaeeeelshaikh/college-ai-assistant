import { useState, useEffect } from 'react';
import { chatSessionAPI } from '../services/api';

export const useChatSessions = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [currentMessages, setCurrentMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadSessions = async () => {
    try {
      const response = await chatSessionAPI.getSessions();
      setSessions(response.data.sessions);
    } catch (err) {
      console.error('Failed to load sessions:', err);
      setError('Failed to load chat sessions');
    }
  };

  const createNewSession = async (title = 'New Chat') => {
    try {
      const response = await chatSessionAPI.createSession(title);
      const newSession = response.data;
      setSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
      setCurrentMessages([]);
      return newSession;
    } catch (err) {
      console.error('Failed to create session:', err);
      setError('Failed to create new chat');
      throw err;
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setLoading(true);
      const response = await chatSessionAPI.getSession(sessionId);
      const sessionDetail = response.data;
      
      setCurrentSession(sessionDetail);
      
      // Convert messages to frontend format
      const messages = sessionDetail.messages.flatMap(msg => [
        { type: 'user', content: msg.question, timestamp: msg.timestamp },
        { type: 'ai', content: msg.answer, timestamp: msg.timestamp }
      ]);
      
      setCurrentMessages(messages);
    } catch (err) {
      console.error('Failed to load session:', err);
      setError('Failed to load chat session');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (message) => {
    if (!currentSession) {
      throw new Error('No active chat session');
    }
    setLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = { type: 'user', content: message, timestamp: new Date().toISOString() };
    setCurrentMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatSessionAPI.sendMessage(currentSession.id, message);
      const aiMessage = { 
        type: 'ai', 
        content: response.data.answer, 
        timestamp: response.data.timestamp 
      };
      setCurrentMessages(prev => [...prev, aiMessage]);
      
      // Update session in list (move to top)
      setSessions(prev => {
        const updated = prev.map(s => 
          s.id === currentSession.id 
            ? { ...s, updated_at: new Date().toISOString(), message_count: (s.message_count || 0) + 1 } 
            : s
        );
        return updated.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send message');
      // Remove the user message if sending failed
      setCurrentMessages(prev => prev.filter(msg => msg !== userMessage));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateSessionTitle = async (sessionId, title) => {
    try {
      await chatSessionAPI.updateSessionTitle(sessionId, title);
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title } : s));
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession(prev => ({ ...prev, title }));
      }
    } catch (err) {
      console.error('Failed to update session title:', err);
      setError('Failed to update chat title');
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await chatSessionAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession(null);
        setCurrentMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
      setError('Failed to delete chat session');
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  return {
    sessions,
    currentSession,
    currentMessages,
    loading,
    error,
    createNewSession,
    loadSession,
    sendMessage,
    updateSessionTitle,
    deleteSession,
    loadSessions
  };
};