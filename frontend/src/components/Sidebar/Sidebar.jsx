import React from 'react';
import { MessageSquare, Plus } from 'lucide-react';

const Sidebar = ({ onNewChat }) => {
  return (
    <div className="w-64 bg-gray-900 text-white h-full flex flex-col">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>New Chat</span>
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-4">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 px-3 py-2 text-gray-300 text-sm">
            <MessageSquare className="h-4 w-4" />
            <span>Chat History</span>
          </div>
          <div className="text-xs text-gray-500 px-3">
            Your conversation history will appear here
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
