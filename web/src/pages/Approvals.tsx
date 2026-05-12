import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import Card from '../components/Card';
import StatusBadge, { getVariant } from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import ErrorBoundary from '../components/ErrorBoundary';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export default function Approvals() {
  const qc = useQueryClient();
  const { apiKey } = useAuth();
  const [tab, setTab] = useState<'pending' | 'history'>('pending');

  const pendingQ = useQuery({
    queryKey: ['approvals-pending'],
    queryFn: api.approval.pending,
    refetchInterval: 10000,
  });
  const historyQ = useQuery({
    queryKey: ['approvals-history'],
    queryFn: api.approval.history,
    enabled: tab === 'history',
  });

  const decideMut = useMutation({
    mutationFn: ({ id, approve, feedback }: { id: string; approve: boolean; feedback: string }) =>
      api.approval.decide(id, { 决策者: apiKey ? 'api_user' : 'api_user', 批准: approve, 反馈: feedback }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals-pending'] });
      qc.invalidateQueries({ queryKey: ['approvals-history'] });
    },
  });

  const [feedbackMap, setFeedbackMap] = useState<Record<string, string>>({});

  const data = tab === 'pending' ? pendingQ.data : historyQ.data;
  const isLoading = tab === 'pending' ? pendingQ.isLoading : historyQ.isLoading;
  const error = tab === 'pending' ? pendingQ.error : historyQ.error;
  const items = (data?.待处理审批列表 ?? (data as unknown as Record<string, unknown>)?.审批历史 ?? []) as Array<{
    ID: string; 流水线ID: string; 阶段ID: string; 状态: string; 风险级别: string; 创建时间: string;
  }>;

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay message={error.message} />;

  return (
    <ErrorBoundary><div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-dark-100">审批管理</h2>
        <div className="flex gap-1 bg-dark-800/60 rounded-md p-0.5">
          <button
            onClick={() => setTab('pending')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              tab === 'pending' ? 'bg-accent-700/60 text-white' : 'text-dark-400 hover:text-dark-200'
            }`}
          >
            待处理 {pendingQ.data?.总数 ? `(${pendingQ.data.总数})` : ''}
          </button>
          <button
            onClick={() => setTab('history')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              tab === 'history' ? 'bg-accent-700/60 text-white' : 'text-dark-400 hover:text-dark-200'
            }`}
          >
            历史
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <Card>
          <p className="text-sm text-dark-500 text-center py-8">
            {tab === 'pending' ? '暂无待处理审批' : '暂无审批历史'}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map(item => {
            const riskVariant = getVariant(
              item.风险级别 === 'high' ? 'danger' : item.风险级别 === 'medium' ? 'warning' : 'success'
            );
            const riskLabel: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' };

            return (
              <div key={item.ID} className="card-hover">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={item.状态} />
                      <span className={`badge ${riskVariant === 'danger' ? 'badge-danger' : riskVariant === 'warning' ? 'badge-warning' : 'badge-success'}`}>
                        {riskLabel[item.风险级别] ?? item.风险级别}
                      </span>
                    </div>
                    <p className="text-xs text-dark-500 font-mono">{item.ID}</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-dark-500">
                    <Clock className="w-3.5 h-3.5" />
                    {item.创建时间}
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs text-dark-400 mb-3">
                  <span>流水线: <span className="text-dark-200 font-mono">{item.流水线ID}</span></span>
                  <span>阶段: <span className="text-dark-200 font-mono">{item.阶段ID}</span></span>
                </div>

                {item.状态 === 'pending' && (
                  <div className="flex items-center gap-3 pt-3 border-t border-dark-700/30">
                    <input
                      type="text"
                      placeholder="反馈（可选）"
                      value={feedbackMap[item.ID] ?? ''}
                      onChange={e => setFeedbackMap(prev => ({ ...prev, [item.ID]: e.target.value }))}
                      className="input flex-1 text-xs py-1.5"
                    />
                    <button
                      onClick={() => decideMut.mutate({ id: item.ID, approve: true, feedback: feedbackMap[item.ID] ?? '' })}
                      disabled={decideMut.isPending}
                      className="btn-success flex items-center gap-1 text-xs py-1.5"
                    >
                      <CheckCircle className="w-3.5 h-3.5" /> 批准
                    </button>
                    <button
                      onClick={() => decideMut.mutate({ id: item.ID, approve: false, feedback: feedbackMap[item.ID] ?? '' })}
                      disabled={decideMut.isPending}
                      className="btn-danger flex items-center gap-1 text-xs py-1.5"
                    >
                      <XCircle className="w-3.5 h-3.5" /> 拒绝
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div></ErrorBoundary>
  );
}
