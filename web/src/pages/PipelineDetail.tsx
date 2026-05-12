import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import ErrorBoundary from '../components/ErrorBoundary';
import { Play, XCircle, ArrowLeft, GitBranch, Layers, Package } from 'lucide-react';

export default function PipelineDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const pipelineQ = useQuery({
    queryKey: ['pipeline', id],
    queryFn: () => api.pipeline.get(id!),
    enabled: !!id,
  });
  const stagesQ = useQuery({
    queryKey: ['pipeline-stages', id],
    queryFn: () => api.pipeline.stages(id!),
    enabled: !!id,
  });
  const artifactsQ = useQuery({
    queryKey: ['pipeline-artifacts', id],
    queryFn: () => api.pipeline.artifacts(id!),
    enabled: !!id,
  });

  const runMut = useMutation({
    mutationFn: () => api.pipeline.run(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline', id] }),
  });
  const cancelMut = useMutation({
    mutationFn: () => api.pipeline.cancel(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline', id] }),
  });

  if (pipelineQ.isLoading) return <Loading />;
  if (pipelineQ.error) return <ErrorDisplay message={pipelineQ.error.message} onRetry={() => pipelineQ.refetch()} />;

  const p = pipelineQ.data!;

  return (
    <ErrorBoundary><div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/pipelines" className="text-dark-400 hover:text-dark-200">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <GitBranch className="w-5 h-5 text-cyber-blue" />
        <h2 className="text-lg font-semibold text-dark-100">{p.名称}</h2>
        <StatusBadge status={p.状态} />
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <p className="text-xs text-dark-500 mb-1">ID</p>
          <p className="text-sm text-dark-200 font-mono">{p.ID}</p>
        </Card>
        <Card>
          <p className="text-xs text-dark-500 mb-1">阶段进度</p>
          <p className="text-sm text-dark-200 font-mono">{p.完成阶段数} / {p.阶段数}</p>
          {p.阶段数 > 0 && (
            <div className="mt-2 h-1.5 bg-dark-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-600 rounded-full transition-all"
                style={{ width: `${(p.完成阶段数 / p.阶段数) * 100}%` }}
              />
            </div>
          )}
        </Card>
        <Card>
          <p className="text-xs text-dark-500 mb-1">操作</p>
          <div className="flex gap-2">
            {(p.状态 === 'pending' || p.状态 === 'failed') && (
              <button onClick={() => runMut.mutate()} disabled={runMut.isPending} className="btn-success text-xs py-1.5">
                <Play className="w-3 h-3 inline mr-1" /> 运行
              </button>
            )}
            {p.状态 === 'running' && (
              <button onClick={() => cancelMut.mutate()} disabled={cancelMut.isPending} className="btn-danger text-xs py-1.5">
                <XCircle className="w-3 h-3 inline mr-1" /> 取消
              </button>
            )}
          </div>
        </Card>
      </div>

      <Card title="阶段列表">
        <div className="flex items-center gap-2 text-dark-500">
          <Layers className="w-4 h-4" />
          <span className="text-sm">
            {(stagesQ.data as Record<string, unknown>)?.阶段列表
              ? `${Array.isArray((stagesQ.data as Record<string, unknown>)?.阶段列表) ? ((stagesQ.data as Record<string, unknown>)?.阶段列表 as unknown[]).length : 0} 个阶段`
              : '暂无阶段信息'}
          </span>
        </div>
      </Card>

      <Card title="制品">
        <div className="flex items-center gap-2 text-dark-500">
          <Package className="w-4 h-4" />
          <span className="text-sm">
            {(artifactsQ.data as Record<string, unknown>)?.制品列表
              ? `${Array.isArray((artifactsQ.data as Record<string, unknown>)?.制品列表) ? ((artifactsQ.data as Record<string, unknown>)?.制品列表 as unknown[]).length : 0} 个制品`
              : '暂无制品信息'}
          </span>
        </div>
      </Card>
    </div></ErrorBoundary>
  );
}
