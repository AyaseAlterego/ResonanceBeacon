import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog } from '@headlessui/react';
import { api } from '../api/client';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import { Link } from 'react-router-dom';
import { Play, XCircle, GitBranch, ChevronRight, Plus } from 'lucide-react';

export default function Pipelines() {
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ['pipelines'], queryFn: api.pipeline.list });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const createMut = useMutation({
    mutationFn: (body: { 名称: string; 描述: string; 流水线定义: Record<string, unknown> }) => api.pipeline.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pipelines'] });
      setDialogOpen(false);
      setNewName('');
      setNewDesc('');
    },
  });

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
        <div className="flex items-center gap-3">
          <span className="text-xs text-dark-400">共 {data?.总数 ?? 0} 条</span>
          <button onClick={() => setDialogOpen(true)}
            className="flex items-center gap-1.5 text-xs py-1.5 px-3 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] transition-shadow">
            <Plus className="w-3 h-3" /> 新建流水线
          </button>
        </div>
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/60" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-[#1a1a2e] border border-white/[0.06] rounded-xl p-6 w-full max-w-md shadow-2xl">
            <Dialog.Title className="text-base font-semibold text-dark-100 mb-4">新建流水线</Dialog.Title>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-dark-400 mb-1">名称</label>
                <input value={newName} onChange={e => setNewName(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-sm text-dark-100 outline-none focus:border-[#6c5ce7]/40 placeholder:text-dark-500"
                  placeholder="流水线名称" />
              </div>
              <div>
                <label className="block text-xs text-dark-400 mb-1">描述</label>
                <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={3}
                  className="w-full bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-sm text-dark-100 outline-none focus:border-[#6c5ce7]/40 placeholder:text-dark-500 resize-none"
                  placeholder="可选描述" />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setDialogOpen(false)}
                className="text-xs py-1.5 px-4 rounded-lg border border-white/[0.06] text-dark-400 hover:text-dark-200 hover:border-white/[0.12]">
                取消
              </button>
              <button onClick={() => createMut.mutate({ 名称: newName, 描述: newDesc, 流水线定义: {} })}
                disabled={!newName.trim() || createMut.isPending}
                className="text-xs py-1.5 px-4 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white disabled:opacity-50 hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] transition-shadow">
                {createMut.isPending ? '创建中...' : '创建'}
              </button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div>
  );
}
