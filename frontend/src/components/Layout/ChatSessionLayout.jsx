import React, { useEffect } from 'react';
import Header from './Header';
import ChatSessionsSidebar from '../Sidebar/ChatSessionsSidebar';
import ChatInterface from '../Chat/ChatInterface';
import { useChatSessions } from '../../hooks/useChatSessions';

const ChatSessionLayout = () => {
  const {
    sessions,
    currentSession,
    currentMessages,
    loading,
    error,
    createNewSession,
    loadSession,
    sendMessage,
    updateSessionTitle,
    deleteSession
  } = useChatSessions();

  const handleNewChat = async () => {
    try {
      await createNewSession();
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleSelectSession = async (sessionId) => {
    try {
      await loadSession(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  // Auto-create first session if none exist
  useEffect(() => {
    if (sessions.length === 0) {
      createNewSession();
    }
  }, [sessions.length]);

  return (
    <div className="h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <ChatSessionsSidebar
          sessions={sessions}
          currentSession={currentSession}
          onNewChat={handleNewChat}
          onSelectSession={handleSelectSession}
          onUpdateTitle={updateSessionTitle}
          onDeleteSession={deleteSession}
        />
        <ChatInterface
          messages={currentMessages}
          onSendMessage={sendMessage}
          loading={loading}
          error={error}
          currentSession={currentSession}
        />
      </div>
    </div>
  );
};

export default ChatSessionLayout;