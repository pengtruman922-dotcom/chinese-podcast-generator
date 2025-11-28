import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../../contexts/UserContext';
import { User, LogOut, ChevronDown, Settings } from 'lucide-react';

const UserMenu: React.FC = () => {
  const { user, logout } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="relative" ref={menuRef}>
      <button
        className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-all duration-200 px-4 py-2.5 rounded-full hover:bg-gray-50 border border-transparent hover:border-gray-200"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="w-8 h-8 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
          <User size={16} className="text-gray-600" />
        </div>
        <span className="hidden md:inline-block max-w-32 truncate font-medium">{user.email}</span>
        <ChevronDown size={16} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-3 w-64 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-100 py-2 z-50 animate-in slide-in-from-top-2 duration-200">
          <div className="px-5 py-3 border-b border-gray-100">
            <div className="text-sm font-semibold text-gray-900">{user.email}</div>
            <div className="text-xs text-gray-500 mt-1 flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${user.isAdmin ? 'bg-purple-500' : 'bg-green-500'}`}></div>
              {user.isAdmin ? '管理员' : '普通用户'}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-5 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-all duration-200 font-medium"
          >
            <LogOut size={16} className="mr-3 text-gray-500" />
            退出登录
          </button>
        </div>
      )}
    </div>
  );
};

export default UserMenu;