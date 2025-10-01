import React from 'react';
import Header from './Header';
import Sidebar from '../Sidebar/Sidebar';
import ChatInterface from '../Chat/ChatInterface';
import { useChat } from '../../hooks/useChat';

const Layout = () => {
  const { clearChat } = useChat();

  const handleNewChat = () => {
    clearChat();
  };

  return (
    <div className="h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar onNewChat={handleNewChat} />
        <ChatInterface onNewChat={handleNewChat} />
      </div>
    </div>
  );
};

export default Layout;
