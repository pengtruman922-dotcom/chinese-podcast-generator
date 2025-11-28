import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

interface TaskDetails {
  task: {
    task_id: string;
    status: string;
    message: string;
    created_at: string;
    file_name?: string;
    result_file?: string;
    error?: string;
  };
  asr_result: any;
  dialogues: Array<{
    speaker: string;
    text: string;
  }>;
}

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [details, setDetails] = useState<TaskDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'asr' | 'translation'>('asr');

  useEffect(() => {
    if (taskId) {
      fetchTaskDetails();
    }
  }, [taskId]);

  const fetchTaskDetails = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/details`);
      if (response.ok) {
        const data = await response.json();
        setDetails(data);
      }
    } catch (error) {
      console.error('Failed to fetch task details:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'processing': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return colorMap[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      'pending': '等待中',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败'
    };
    return statusMap[status] || status;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <svg className="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">加载任务详情失败</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-blue-600 hover:underline"
        >
          返回任务列表
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* 头部 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:underline mb-4 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回任务列表
        </button>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {details.task.file_name || '未知文件'}
              </h1>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(details.task.status)}`}>
                  {getStatusText(details.task.status)}
                </span>
                <span>{details.task.message}</span>
                <span>创建于: {formatDate(details.task.created_at)}</span>
              </div>
            </div>
            {details.task.result_file && (
              <button
                onClick={() => window.open(`${API_BASE_URL}/api/download/${details.task.result_file}`, '_blank')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                下载结果
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('asr')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'asr'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ASR识别结果
            </button>
            <button
              onClick={() => setActiveTab('translation')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'translation'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              翻译结果
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'asr' && (
            <div>
              {details.asr_result?.result?.utterances ? (
                <div className="space-y-4">
                  <div className="text-sm text-gray-600 mb-4">
                    共识别出 {details.asr_result.result.utterances.length} 段对话
                  </div>
                  {details.asr_result.result.utterances.map((utterance: any, index: number) => {
                    const speaker = utterance.speaker || utterance.additions?.speaker || 'unknown';
                    const gender = utterance.additions?.gender;
                    
                    return (
                      <div key={index} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2 text-sm">
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
                            Speaker {speaker}
                          </span>
                          {gender && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                              {gender}
                            </span>
                          )}
                          {utterance.start_time !== undefined && (
                            <span className="text-gray-500">
                              {(utterance.start_time / 1000).toFixed(2)}s - {(utterance.end_time / 1000).toFixed(2)}s
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800">{utterance.text}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  暂无ASR识别结果
                </div>
              )}
            </div>
          )}

          {activeTab === 'translation' && (
            <div>
              {details.dialogues && details.dialogues.length > 0 ? (
                <div className="space-y-4">
                  <div className="text-sm text-gray-600 mb-4">
                    共 {details.dialogues.length} 段中文对话
                  </div>
                  {details.dialogues.map((dialogue, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          dialogue.speaker === '发言者1' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          {dialogue.speaker}
                        </span>
                      </div>
                      <p className="text-gray-800 leading-relaxed">{dialogue.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  暂无翻译结果
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskDetailPage;
