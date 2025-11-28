import React from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../../contexts/UserContext';
import { Play, Languages, Settings } from 'lucide-react';
import UserMenu from './UserMenu';

const Header: React.FC = () => {
  const { user } = useUser();

  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center max-w-7xl">
        <Link to="/" className="flex items-center space-x-3 text-xl font-semibold text-gray-900 hover:text-gray-700 transition-all duration-200 group">
          <div className="relative w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-500 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative flex items-center justify-center">
              <Play size={16} className="text-white fill-white mr-0.5" />
              <Languages size={12} className="text-white/80 ml-0.5" />
            </div>
          </div>
          <span className="bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">TransTube</span>
        </Link>
        
        {user ? (
          <div className="flex items-center space-x-8">
            <nav className="hidden md:flex space-x-8">
              <Link
                to="/tasks"
                className="text-gray-600 hover:text-gray-900 transition-all duration-200 px-4 py-2 rounded-xl hover:bg-gray-50 font-medium"
              >
                我的任务
              </Link>
              <Link
                to="/settings"
                className="text-gray-600 hover:text-gray-900 transition-all duration-200 px-4 py-2 rounded-xl hover:bg-gray-50 font-medium flex items-center gap-2"
              >
                <Settings size={18} />
                设置
              </Link>
              {user.isAdmin && (
                <Link
                  to="/admin"
                  className="text-gray-600 hover:text-gray-900 transition-all duration-200 px-4 py-2 rounded-xl hover:bg-gray-50 font-medium"
                >
                  管理
                </Link>
              )}
            </nav>
            <UserMenu />
          </div>
        ) : (
          <Link
            to="/login"
            className="inline-flex items-center px-6 py-2.5 border border-transparent text-sm font-semibold rounded-full text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            登录
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;