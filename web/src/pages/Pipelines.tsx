import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import { Link } from 'react-router-dom';
import { Play, XCircle, GitBranch, ChevronRight } from 'lucide-react';

export default function Pipelines() {
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ['pipelines'], queryFn: api.pipeline.list });

  const runMut = useMutation({
    mutationFn: (id: string) => api.pipeline.run(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipelines'] }),
  });
  const cancelMut = useMutation({
    mutationFn: (id: string) => api.pipeline.cancel(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipelines'] }),
  });

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay message={error.message} onRetry={() => refetch()} />;

  const pipelines = data?.流水线列表 ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-dark-100">流水线列表</h2>
        <span className="text-xs text-dark-400">共 {data?.总数 ?? 0} 条</span>
      </div>

      {pipelines.length === 0 ? (
        <Card>
          <p className="text-sm text-dark-500 text-center py-8">暂无流水线数据</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {pipelines.map(p => (
            <div key={p.ID} className="card-hover flex items-center justify-between">
              <div className="flex items-center gap-4 min-w-0">
                <GitBranch className="w-4 h-4 text-dark-400 shrink-0" />
                <div className="min-w-0">
                  <Link to={`/pipelines/${p.ID}`} className="text-sm text-dark-100 hover:text-accent-400 transition-colors truncate block">
                    {p.名称}
                  </Link>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-dark-500 font-mono">{p.ID}</span>
                    {p.阶段数 > 0 && (
                      <span className="text-xs text-dark-500">
                        阶段 {p.完成阶段数}/{p.阶段数}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <StatusBadge status={p.状态} />
                {p.状态 === 'pending' && (
                  <button
                    onClick={() => runMut.mutate(p.ID)}
                    disabled={runMut.isPending}
                    className="btn-success flex items-center gap-1.5 text-xs py-1.5 px-3"
                  >
                    <Play className="w-3 h-3" /> 运行
                  </button>
                )}
                {p.状态 === 'running' && (
                  <button
                    onClick={() => cancelMut.mutate(p.ID)}
                    disabled={cancelMut.isPending}
                    className="btn-danger flex items-center gap-1.5 text-xs py-1.5 px-3"
                  >
                    <XCircle className="w-3 h-3" /> 取消
                  </button>
                )}
                <Link to={`/pipelines/${p.ID}`} className="text-dark-400 hover:text-dark-200">
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
