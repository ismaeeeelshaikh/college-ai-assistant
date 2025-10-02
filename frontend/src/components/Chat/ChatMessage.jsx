import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';

const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-primary-600 text-white' : 'bg-gray-50 border border-gray-200'
          }`}>
            {isUser ? (
              <User className="h-4 w-4" />
            ) : (
              /* UPDATED: Use your logo for AI messages */
              <>
                <img 
                  src="/logo.png" 
                  alt="Smart Campus Connect" 
                  className="w-6 h-6 object-contain"
                  onError={(e) => {
                    // Fallback if logo doesn't load
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                <Bot className="h-4 w-4 text-gray-600" style={{display: 'none'}} />
              </>
            )}
          </div>
        </div>
        
        <div className={`rounded-lg px-4 py-2 ${
          isUser 
            ? 'bg-primary-600 text-white' 
            : 'bg-white border border-gray-200 text-gray-900'
        }`}>
          {isUser ? (
            <p className="text-sm">{message.content}</p>
          ) : (
            <div className="text-sm prose prose-sm max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          <div className={`text-xs mt-1 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;