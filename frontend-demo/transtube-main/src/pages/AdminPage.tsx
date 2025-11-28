import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';
import { Trash2, Search, Download, Filter, Loader2, RefreshCw, BarChart3 } from 'lucide-react';
import Button from '../components/UI/Button';
import StatusBadge from '../components/UI/StatusBadge';

interface AdminTask {
  id: string;
  fileName: string;
  fileSize?: number;
  title: string;
  duration: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  errorCode?: string;
  createdAt: string;
  updatedAt: string;
  userId: string;
  userEmail: string;
  retryCount: number;
}

const AdminPage: React.FC = () => {
  const { user, isLoading } = useUser();
  const [tasks, setTasks] = useState<AdminTask[]>([]);
  const [isTasksLoading, setIsTasksLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const fetchAdminTasks = async () => {
      try {
        setIsTasksLoading(true);
        await new Promise((resolve) => setTimeout(resolve, 1000));
        
        const mockTasks: AdminTask[] = Array.from({ length: 12 }).map((_, index) => ({
          id: (index + 1).toString(),
          fileName: `audio-file-${index + 1}.${['mp3', 'wav', 'm4a'][index % 3]}`,
          fileSize: Math.floor(Math.random() * 50000000) + 10000000, // 10MB-60MB
          title: [
            '如何使用React构建现代Web应用',
            '2023年AI发展趋势分析',
            '高效学习英语的10个技巧',
            '深度学习入门指南',
            '产品经理必备技能培养',
            '数据分析师职业规划',
            '前端开发最佳实践',
            '科技创新与未来展望',
            '有效沟通的艺术',
            '领导力培养与团队管理',
            'JavaScript高级编程技巧',
            '用户体验设计原则'
          ][index],
          duration: [1245, 2430, 1830, 3660, 1500, 2700, 1920, 3000, 2100, 2800, 1680, 2250][index],
          status: ['completed', 'processing', 'queued', 'failed', 'completed', 'completed', 'processing', 'failed', 'completed', 'queued', 'processing', 'completed'][index % 12] as any,
          errorCode: [3, 7].includes(index) ? 'REGION_RESTRICTED' : undefined,
          createdAt: new Date(Date.now() - 86400000 * (index % 7)).toISOString(),
          updatedAt: new Date(Date.now() - 86000000 * (index % 7)).toISOString(),
          userId: ['user1', 'user2', 'user3', 'user4', 'user5'][index % 5],
          userEmail: [`user${(index % 5) + 1}@example.com`],
          retryCount: [3, 7].includes(index) ? 1 : 0,
        }));
        setTasks(mockTasks);
      } catch (error) {
        console.error('Failed to fetch admin tasks:', error);
      } finally {
        setIsTasksLoading(false);
      }
    };

    fetchAdminTasks();
  }, []);

  const handleRetryTask = async (taskId: string) => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setTasks(
        tasks.map((task) =>
          task.id === taskId
            ? {
                ...task,
                status: 'queued',
                errorCode: undefined,
                retryCount: task.retryCount + 1,
                updatedAt: new Date().toISOString(),
              }
            : task
        )
      );
    } catch (error) {
      console.error('Failed to retry task:', error);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('确定要删除此任务吗？此操作不可恢复。')) {
      return;
    }

    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setTasks(tasks.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      alert('数据导出成功！');
    } catch (error) {
      console.error('Failed to export data:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.fileName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.userEmail.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((task) => task.status === 'completed').length;
  const failedTasks = tasks.filter((task) => task.status === 'failed').length;
  const processingTasks = tasks.filter((task) => task.status === 'processing').length;
  const successRate = totalTasks > 0 ? ((completedTasks / totalTasks) * 100).toFixed(1) : '0';

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 size={48} className="text-blue-500 animate-spin" />
      </div>
    );
  }

  // Redirect if not admin
  if (!user || !user.isAdmin) {
    return <Navigate to="/tasks" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">管理控制台</h1>
        <p className="text-gray-600 mt-1">系统任务管理和数据统计</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 size={24} className="text-blue-600" />
            </div>
            <div className="ml-4">
              <div className="text-sm text-gray-600">总任务数</div>
              <div className="text-2xl font-bold text-gray-900">{totalTasks}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <BarChart3 size={24} className="text-green-600" />
            </div>
            <div className="ml-4">
              <div className="text-sm text-gray-600">完成任务</div>
              <div className="text-2xl font-bold text-green-600">{completedTasks}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <BarChart3 size={24} className="text-red-600" />
            </div>
            <div className="ml-4">
              <div className="text-sm text-gray-600">失败任务</div>
              <div className="text-2xl font-bold text-red-600">{failedTasks}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 size={24} className="text-blue-600" />
            </div>
            <div className="ml-4">
              <div className="text-sm text-gray-600">成功率</div>
              <div className="text-2xl font-bold text-gray-900">{successRate}%</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-grow">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search size={18} className="text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="搜索文件名、标题或用户邮箱..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Filter size={18} className="text-gray-400" />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="block pl-10 pr-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none bg-white min-w-32"
              >
                <option value="all">所有状态</option>
                <option value="queued">排队中</option>
                <option value="processing">处理中</option>
                <option value="completed">已完成</option>
                <option value="failed">失败</option>
              </select>
            </div>
            
            <Button onClick={handleExportData} variant="secondary" isLoading={isExporting}>
              <Download size={16} className="mr-1" />
              导出数据
            </Button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {isTasksLoading ? (
          <div className="flex justify-center items-center py-24">
            <Loader2 size={48} className="text-blue-500 animate-spin" />
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-24 text-gray-500">
            没有找到匹配的任务
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    任务信息
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    创建时间
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTasks.map((task) => (
                  <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="max-w-xs">
                        <div className="text-sm font-medium text-gray-900 mb-1 line-clamp-2">
                          {task.title}
                        </div>
                        <div className="text-xs text-gray-500 mb-1">
                          时长: {formatDuration(task.duration)}
                        </div>
                        {task.fileSize && (
                          <div className="text-xs text-gray-500 mb-1">
                            大小: {formatFileSize(task.fileSize)}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 truncate">
                          {task.fileName}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{task.userEmail}</div>
                      <div className="text-xs text-gray-500">ID: {task.userId}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <StatusBadge status={task.status} />
                        {task.errorCode && (
                          <div className="text-xs text-red-600">
                            错误: {task.errorCode}
                          </div>
                        )}
                        {task.retryCount > 0 && (
                          <div className="text-xs text-gray-500">
                            已重试: {task.retryCount}次
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(task.createdAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex justify-end space-x-2">
                        {task.status === 'failed' && (
                          <button
                            onClick={() => handleRetryTask(task.id)}
                            className="text-blue-600 hover:text-blue-900 transition-colors p-1"
                            title="重试任务"
                          >
                            <RefreshCw size={16} />
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteTask(task.id)}
                          className="text-red-600 hover:text-red-900 transition-colors p-1"
                          title="删除任务"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPage;