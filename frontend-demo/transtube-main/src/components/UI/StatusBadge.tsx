import React from 'react';
import { Clock, Circle, CheckCircle, XCircle } from 'lucide-react';

export type TaskStatus = 'queued' | 'processing' | 'completed' | 'failed';

interface StatusBadgeProps {
  status: TaskStatus;
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'queued':
        return {
          label: '排队中',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-600',
          icon: <Clock size={16} className="mr-1" />,
        };
      case 'processing':
        return {
          label: '处理中',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-600',
          icon: <Circle size={16} className="mr-1" />,
        };
      case 'completed':
        return {
          label: '完成',
          bgColor: 'bg-green-100',
          textColor: 'text-green-600',
          icon: <CheckCircle size={16} className="mr-1" />,
        };
      case 'failed':
        return {
          label: '处理失败',
          bgColor: 'bg-red-100',
          textColor: 'text-red-600',
          icon: <XCircle size={16} className="mr-1" />,
        };
      default:
        return {
          label: '未知',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-600',
          icon: null,
        };
    }
  };

  const { label, bgColor, textColor, icon } = getStatusConfig();

  return (
    <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ${bgColor} ${textColor} ${className} shadow-sm`}>
      {icon}
      {label}
    </span>
  );
};

export default StatusBadge;