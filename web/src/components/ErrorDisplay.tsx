import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-dark-400">
      <AlertCircle className="w-8 h-8 text-cyber-red mb-3" />
      <p className="text-sm text-dark-300 mb-3">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" />
          重试
        </button>
      )}
    </div>
  );
}
