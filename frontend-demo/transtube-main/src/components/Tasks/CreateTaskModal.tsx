import React, { useState } from 'react';
import { X, CheckCircle, AlertCircle, Loader2, Upload, File, Music } from 'lucide-react';
import Button from '../UI/Button';

interface TaskInfo {
  id: string;
  fileName: string;
  fileSize: number;
  title: string;
  duration: number;
  thumbnailUrl: string;
  status: 'queued';
  createdAt: string;
  updatedAt: string;
}

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTaskCreated: (task: TaskInfo) => void;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  onTaskCreated,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [step, setStep] = useState<'input' | 'preview' | 'submitting'>('input');
  const [error, setError] = useState('');
  const [videoInfo, setVideoInfo] = useState<{
    title: string;
    duration: number;
    thumbnailUrl: string;
    fileSize: number;
  } | null>(null);

  if (!isOpen) return null;

  const handleClose = () => {
    setSelectedFile(null);
    setStep('input');
    setError('');
    setVideoInfo(null);
    onClose();
  };

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!selectedFile) {
      setError('请选择音频文件');
      return;
    }

    // 检查文件类型
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a'];
    const allowedExtensions = ['.mp3', '.wav', '.m4a'];
    const fileExtension = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(selectedFile.type) && !allowedExtensions.includes(fileExtension)) {
      setError('请选择支持的音频格式（MP3、WAV、M4A）');
      return;
    }

    // 检查文件大小（限制为100MB）
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError('文件大小不能超过100MB');
      return;
    }

    try {
      setStep('submitting');
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      const mockVideoInfo = {
        title: selectedFile.name.replace(/\.[^/.]+$/, ''), // 移除文件扩展名作为标题
        duration: Math.floor(Math.random() * 3600) + 300, // 随机时长5分钟到1小时
        thumbnailUrl: 'https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=480&h=270&dpr=1',
        fileSize: selectedFile.size,
      };
      setVideoInfo(mockVideoInfo);
      setStep('preview');
    } catch (err) {
      setError('无法解析音频文件信息，请重试');
      setStep('input');
    }
  };

  const handleSubmitTask = async () => {
    if (!videoInfo) return;

    setStep('submitting');
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      const newTask: TaskInfo = {
        id: Date.now().toString(),
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        title: videoInfo.title,
        duration: videoInfo.duration,
        thumbnailUrl: videoInfo.thumbnailUrl,
        status: 'queued',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      onTaskCreated(newTask);
    } catch (err) {
      setError('创建任务失败，请重试');
      setStep('preview');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-900 opacity-50"></div>
        </div>
        
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
          &#8203;
        </span>
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-6 pt-6 pb-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                {step === 'input' ? '新建任务' : step === 'preview' ? '确认音频信息' : '提交中'}
              </h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 transition-colors"
                onClick={handleClose}
              >
                <X size={24} />
              </button>
            </div>

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start">
                <AlertCircle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {step === 'input' && (
              <form onSubmit={handleFileSubmit}>
                <div className="mb-6">
                  <label htmlFor="audio-file" className="block text-sm font-semibold text-gray-800 mb-3">
                    选择音频文件
                  </label>
                  
                  <div className="relative">
                    <input
                      id="audio-file"
                      type="file"
                      accept=".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/mp4,audio/x-m4a"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <label
                      htmlFor="audio-file"
                      className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-200 border-dashed rounded-2xl cursor-pointer bg-gray-50 hover:bg-gray-100 transition-all duration-200"
                    >
                      {selectedFile ? (
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                            <Music size={24} className="text-blue-600" />
                          </div>
                          <div className="text-left">
                            <div className="text-sm font-medium text-gray-900 truncate max-w-48">
                              {selectedFile.name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {formatFileSize(selectedFile.size)}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center">
                          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-3">
                            <Upload size={24} className="text-blue-600" />
                          </div>
                          <div className="text-sm font-medium text-gray-900 mb-1">
                            点击选择音频文件
                          </div>
                          <div className="text-xs text-gray-500">
                            支持 MP3、WAV、M4A 格式
                          </div>
                        </div>
                      )}
                    </label>
                  </div>
                  
                  <p className="mt-2 text-xs text-gray-500">
                    支持 MP3、WAV、M4A 格式，文件大小不超过100MB
                  </p>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:space-x-3 space-y-3 sm:space-y-0">
                  <Button type="submit" variant="primary" fullWidth isLoading={step === 'submitting'}>
                    <File size={16} className="mr-1" />
                    解析音频
                  </Button>
                  <Button type="button" variant="secondary" onClick={handleClose} fullWidth>
                    取消
                  </Button>
                </div>
              </form>
            )}

            {step === 'preview' && videoInfo && (
              <div>
                <div className="mb-6">
                  <img
                    src={videoInfo.thumbnailUrl}
                    alt={videoInfo.title}
                    className="w-full h-48 object-cover rounded-lg"
                  />
                </div>
                
                <div className="mb-6 space-y-3">
                  <div>
                    <h4 className="text-base font-medium text-gray-900 mb-1">
                      {videoInfo.title}
                    </h4>
                    <p className="text-sm text-gray-600">
                      文件大小: {formatFileSize(videoInfo.fileSize)}
                    </p>
                    <p className="text-sm text-gray-600">
                      时长: {formatDuration(videoInfo.duration)}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                      文件名: {selectedFile?.name}
                    </p>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:space-x-3 space-y-3 sm:space-y-0">
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleSubmitTask}
                    fullWidth
                    isLoading={step === 'submitting'}
                  >
                    <CheckCircle size={16} className="mr-1" />
                    确认提交
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setStep('input')}
                    fullWidth
                  >
                    返回修改
                  </Button>
                </div>
              </div>
            )}

            {step === 'submitting' && !videoInfo && (
              <div className="py-12 flex flex-col items-center justify-center">
                <Loader2 size={48} className="text-blue-500 animate-spin mb-4" />
                <p className="text-gray-600">正在解析音频信息...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateTaskModal;