import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { AutonomousLoopStatus, AutonomousLoopEvent } from '../types';
import { Play, Pause, Square, Activity, Clock, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const 状态配置: Record<string, { 标签: string; 颜色: string; 图标: React.ComponentType<{ className?: string }> }> = {
  idle: { 标签: '空闲', 颜色: 'text-gray-400', 图标: Clock },
  scanning: { 标签: '扫描中', 颜色: 'text-blue-400', 图标: Activity },
  triaging: { 标签: '分诊中', 颜色: 'text-yellow-400', 图标: Activity },
  selecting: { 标签: '选择任务', 颜色: 'text-purple-400', 图标: Activity },
  developing: { 标签: '开发中', 颜色: 'text-green-400', 图标: Activity },
  reviewing_security: { 标签: '安全审查', 颜色: 'text-red-400', 图标: AlertTriangle },
  reviewing_qa: { 标签: '质量验证', 颜色: 'text-orange-400', 图标: CheckCircle },
  awaiting_approval: { 标签: '等待审批', 颜色: 'text-yellow-400', 图标: Clock },
  deploying: { 标签: '部署中', 颜色: 'text-blue-400', 图标: Activity },
  paused: { 标签: '已暂停', 颜色: 'text-gray-500', 图标: Pause },
  error: { 标签: '错误', 颜色: 'text-red-500', 图标: XCircle },
};

export default function AutonomousLoopStatus() {
  const [事件日志, set事件日志] = useState<AutonomousLoopEvent[]>([]);
  const [showLog, setShowLog] = useState(false);

  const statusQ = useQuery({
    queryKey: ['autonomous-loop-status'],
    queryFn: api.autonomousLoop.getStatus,
    refetchInterval: 5000,
    retry: false,
  });

  const logQ = useQuery({
    queryKey: ['autonomous-loop-log'],
    queryFn: () => api.autonomousLoop.getEventLog(20),
    enabled: showLog,
    refetchInterval: showLog ? 3000 : false,
  });

  useEffect(() => {
    if (logQ.data) {
      set事件日志(logQ.data.事件列表);
    }
  }, [logQ.data]);

  const status = statusQ.data as AutonomousLoopStatus | undefined;
  const 状态信息 = status ? 状态配置[status.状态] || 状态配置.idle : null;
  const Icon = 状态信息?.图标 || Clock;

  const handleAction = async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    try {
      switch (action) {
        case 'start': await api.autonomousLoop.start(); break;
        case 'stop': await api.autonomousLoop.stop(); break;
        case 'pause': await api.autonomousLoop.pause(); break;
        case 'resume': await api.autonomousLoop.resume(); break;
      }
      statusQ.refetch();
    } catch (err) {
      console.error(`自主循环${action}失败:`, err);
    }
  };

  if (statusQ.isLoading) {
    return (
      <div className="flex items-center gap-3 p-3 rounded-md bg-black/20">
        <div className="animate-spin w-4 h-4 border-2 border-[#a29bfe] border-t-transparent rounded-full" />
        <span className="text-sm text-[#6b7280]">加载自主循环状态...</span>
      </div>
    );
  }

  if (statusQ.error || !status) {
    return (
      <div className="flex items-center gap-3 p-3 rounded-md bg-black/20">
        <AlertTriangle className="w-4 h-4 text-[#f59e0b]" />
        <span className="text-sm text-[#6b7280]">自主循环引擎未连接</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 状态条 */}
      <div className="flex items-center justify-between p-3 rounded-md bg-black/20">
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${状态信息?.颜色 || 'text-gray-400'}`} />
          <div>
            <div className="text-sm text-white/60">Oh My Hermes CTO Loop</div>
            <div className="flex items-center gap-2">
              <span className={`text-xs ${状态信息?.颜色 || 'text-gray-400'}`}>
                {状态信息?.标签 || '未知'}
              </span>
              {status.运行中 && (
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!status.运行中 || status.状态 === 'paused' ? (
            <button
              onClick={() => handleAction(status.状态 === 'paused' ? 'resume' : 'start')}
              className="p-1.5 rounded hover:bg-white/10 text-green-400"
              title="启动"
            >
              <Play className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => handleAction('pause')}
              className="p-1.5 rounded hover:bg-white/10 text-yellow-400"
              title="暂停"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}
          {status.运行中 && (
            <button
              onClick={() => handleAction('stop')}
              className="p-1.5 rounded hover:bg-white/10 text-red-400"
              title="停止"
            >
              <Square className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setShowLog(!showLog)}
            className="p-1.5 rounded hover:bg-white/10 text-[#6b7280]"
            title="查看日志"
          >
            <Activity className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 配置信息 */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 rounded bg-black/20">
          <span className="text-[#6b7280]">扫描间隔</span>
          <div className="text-white/60">{status.配置.扫描间隔秒}秒</div>
        </div>
        <div className="p-2 rounded bg-black/20">
          <span className="text-[#6b7280]">自动审批</span>
          <div className={status.配置.自动审批 ? 'text-green-400' : 'text-red-400'}>
            {status.配置.自动审批 ? '开启' : '关闭'}
          </div>
        </div>
      </div>

      {/* 事件日志 */}
      {showLog && (
        <div className="rounded-md bg-black/20 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-xs text-[#6b7280]">最近事件</span>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {事件日志.length === 0 ? (
              <div className="p-3 text-xs text-[#6b7280] text-center">暂无事件</div>
            ) : (
              事件日志.map(事件 => (
                <div key={事件.ID} className="px-3 py-2 border-b border-white/5 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/60">{事件.类型}</span>
                    <span className="text-[10px] text-[#6b7280]">
                      {new Date(事件.时间).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-[10px] text-[#6b7280] truncate">{事件.描述}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
