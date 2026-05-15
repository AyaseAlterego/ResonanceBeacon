import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog } from '@headlessui/react';
import { api } from '../api/client';
import Card from '../components/Card';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import ErrorBoundary from '../components/ErrorBoundary';
import { Link } from 'react-router-dom';
import { FolderOpen, Plus } from 'lucide-react';
import type { ProjectStage } from '../types';

const 阶段颜色: Record<string, string> = {
  '需求分析': 'text-blue-400',
  '架构设计': 'text-purple-400',
  '方案确认': 'text-amber-400',
  '开发执行': 'text-green-400',
  '代码审查': 'text-cyan-400',
  '完成': 'text-emerald-400',
  '已取消': 'text-gray-500',
  '失败': 'text-red-400',
};

export default function Projects() {
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ['projects'], queryFn: api.project.list });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const createMut = useMutation({
    mutationFn: (body: { 名称: string; 描述: string }) => api.project.create(body),
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: ['projects'] });
      setDialogOpen(false);
      setNewName('');
      setNewDesc('');
      window.location.hash = `#/projects/${project.ID}`;
    },
  });

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay message={error.message} onRetry={() => refetch()} />;

  const projects = data?.项目列表 ?? [];

  return (
    <ErrorBoundary><div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-dark-100">项目列表</h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-dark-400">共 {data?.总数 ?? 0} 个</span>
          <button onClick={() => setDialogOpen(true)}
            className="flex items-center gap-1.5 text-xs py-1.5 px-3 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] transition-shadow">
            <Plus className="w-3 h-3" /> 新建项目
          </button>
        </div>
      </div>

      {projects.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FolderOpen className="w-12 h-12 text-dark-500 mx-auto mb-3" />
            <p className="text-sm text-dark-500">还没有项目</p>
            <p className="text-xs text-dark-500 mt-1">点击「新建项目」开始与 Hermes 协作</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {projects.map(p => (
            <Link key={p.ID} to={`/projects/${p.ID}`}
              className="card-hover flex items-center justify-between">
              <div className="flex items-center gap-4 min-w-0">
                <FolderOpen className="w-4 h-4 text-dark-400 shrink-0" />
                <div className="min-w-0">
                  <span className="text-sm text-dark-100 hover:text-accent-400 transition-colors truncate block">{p.名称}</span>
                  {p.描述 && <p className="text-xs text-dark-500 mt-0.5 truncate">{p.描述}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`text-xs font-medium ${阶段颜色[p.阶段] || 'text-dark-400'}`}>{p.阶段}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/60" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-[#1a1a2e] border border-white/[0.06] rounded-xl p-6 w-full max-w-md shadow-2xl">
            <Dialog.Title className="text-base font-semibold text-dark-100 mb-4">新建项目</Dialog.Title>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-dark-400 mb-1">名称</label>
                <input value={newName} onChange={e => setNewName(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-sm text-dark-100 outline-none focus:border-[#6c5ce7]/40 placeholder:text-dark-500"
                  placeholder="项目名称" />
              </div>
              <div>
                <label className="block text-xs text-dark-400 mb-1">描述</label>
                <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={3}
                  className="w-full bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-sm text-dark-100 outline-none focus:border-[#6c5ce7]/40 placeholder:text-dark-500 resize-none"
                  placeholder="简单描述你想做什么（可选）" />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setDialogOpen(false)}
                className="text-xs py-1.5 px-4 rounded-lg border border-white/[0.06] text-dark-400 hover:text-dark-200 hover:border-white/[0.12]">
                取消
              </button>
              <button onClick={() => createMut.mutate({ 名称: newName, 描述: newDesc })}
                disabled={!newName.trim() || createMut.isPending}
                className="text-xs py-1.5 px-4 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white disabled:opacity-50 hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] transition-shadow">
                {createMut.isPending ? '创建中...' : '创建'}
              </button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div></ErrorBoundary>
  );
}
