import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';
import { Play, Languages, Mail, Lock, Eye, EyeOff, Sparkles, Loader2 } from 'lucide-react';
import Button from '../components/UI/Button';

const LoginPage: React.FC = () => {
  const [isLoginView, setIsLoginView] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const { user, isLoading, login, register } = useUser();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('请填写所有字段');
      return;
    }

    try {
      if (isLoginView) {
        await login(email, password);
      } else {
        await register(email, password);
      }
      navigate('/tasks');
    } catch (err) {
      setError('操作失败，请重试');
    }
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-80px)]">
        <Loader2 size={48} className="text-blue-500 animate-spin" />
      </div>
    );
  }

  // Redirect if already logged in
  if (user) {
    return <Navigate to="/tasks" />;
  }

  return (
    <div className="min-h-[calc(100vh-80px)] flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-md w-full mx-auto">
        <div className="bg-white/80 backdrop-blur-xl shadow-2xl rounded-3xl p-10 border border-gray-100">
          <div className="text-center mb-8">
            <div className="relative w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-500 rounded-3xl opacity-0 animate-pulse"></div>
              <div className="relative flex items-center justify-center">
                <Play size={24} className="text-white fill-white mr-1" />
                <Languages size={18} className="text-white/90 ml-1" />
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <Sparkles size={12} className="text-white" />
              </div>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-3">
              {isLoginView ? '欢迎回来' : '创建账户'}
            </h2>
            <p className="text-gray-600 text-lg">
              {isLoginView ? '登录您的账户继续使用 TransTube' : '注册新账户开始使用 TransTube'}
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-7">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-800 mb-3">
                邮箱地址
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail size={20} className="text-gray-400" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white text-gray-900 placeholder-gray-500"
                  placeholder="your@email.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-800 mb-3">
                密码
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={20} className="text-gray-400" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-12 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white text-gray-900 placeholder-gray-500"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center hover:bg-gray-100 rounded-r-2xl transition-colors duration-200"
                >
                  {showPassword ? (
                    <EyeOff size={20} className="text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye size={20} className="text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            <Button type="submit" variant="primary" fullWidth isLoading={isLoading} size="lg">
              {isLoginView ? '登录' : '注册'}
            </Button>
          </form>

          <div className="mt-8 text-center">
            <button
              type="button"
              onClick={() => setIsLoginView(!isLoginView)}
              className="text-sm text-blue-600 hover:text-blue-800 transition-colors duration-200 font-medium"
            >
              {isLoginView ? '没有账号？点击注册' : '已有账号？点击登录'}
            </button>
          </div>

          <div className="mt-8 text-center text-xs text-gray-500">
            <p>使用管理员账号登录: admin@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;