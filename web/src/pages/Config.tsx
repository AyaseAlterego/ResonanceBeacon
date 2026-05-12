import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import ErrorBoundary from '../components/ErrorBoundary';
import { Settings, Save, RefreshCw } from 'lucide-react';

export default function Config() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<'current' | 'merged'>('current');
  const [editValue, setEditValue] = useState('');
  const [editKey, setEditKey] = useState('');
  const [saveMsg, setSaveMsg] = useState('');

  const configQ = useQuery({
    queryKey: ['config', tab],
    queryFn: tab === 'current' ? api.config.get : api.config.merged,
  });

  const updateMut = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => api.config.update(key, value),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config'] });
      setSaveMsg('配置已更新');
      setEditKey('');
      setEditValue('');
      setTimeout(() => setSaveMsg(''), 3000);
    },
  });

  if (configQ.isLoading) return <Loading />;
  if (configQ.error) return <ErrorDisplay message={configQ.error.message} onRetry={() => configQ.refetch()} />;

  const config = configQ.data?.配置 ?? {};

  return (
    <ErrorBoundary><div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white/80">配置管理</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/30">来源: {configQ.data?.来源}</span>
          <button onClick={() => configQ.refetch()} className="text-white/40 hover:text-white/70">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex gap-1 bg-[#1a1a2e] rounded-md p-0.5 w-fit">
        <button
          onClick={() => setTab('current')}
          className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            tab === 'current' ? 'bg-[#6c5ce7]/20 text-white' : 'text-white/40 hover:text-white/70'
          }`}
        >
          当前配置
        </button>
        <button
          onClick={() => setTab('merged')}
          className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            tab === 'merged' ? 'bg-[#6c5ce7]/20 text-white' : 'text-white/40 hover:text-white/70'
          }`}
        >
          合并后配置
        </button>
      </div>

      <Card title="配置内容" action={<Settings className="w-4 h-4 text-white/30" />}>
        <div className="space-y-4">
          {Object.entries(config).map(([section, value]) => (
            <div key={section}>
              <h4 className="text-xs font-semibold text-[#a29bfe] mb-2 uppercase tracking-wider">{section}</h4>
              <div className="bg-black/30 rounded-md p-3 font-mono text-xs text-white/60 space-y-1">
                {typeof value === 'object' && value !== null
                  ? Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-2">
                        <span className="text-white/30">{k}:</span>
                        <span className="text-white/70">
                          {typeof v === 'object' && v !== null ? JSON.stringify(v, null, 2) : String(v)}
                        </span>
                      </div>
                    ))
                  : String(value)}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="更新配置">
        {saveMsg && (
          <div className="mb-3 p-2 rounded bg-green-900/20 border border-green-800/30 text-xs text-green-400">
            {saveMsg}
          </div>
        )}
        <div className="space-y-3">
          <div>
            <label className="text-xs text-white/40 mb-1 block">键路径</label>
            <input
              type="text"
              value={editKey}
              onChange={e => setEditKey(e.target.value)}
              placeholder="例: 流水线.默认超时"
              className="w-full px-3 py-2 bg-black/30 border border-white/10 rounded-md text-white/60 placeholder-white/20 focus:outline-none focus:border-[#a29bfe]/60 focus:ring-1 focus:ring-[#a29bfe]/30 text-xs"
            />
          </div>
          <div>
            <label className="text-xs text-white/40 mb-1 block">值</label>
            <input
              type="text"
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              placeholder="例: 600"
              className="w-full px-3 py-2 bg-black/30 border border-white/10 rounded-md text-white/60 placeholder-white/20 focus:outline-none focus:border-[#a29bfe]/60 focus:ring-1 focus:ring-[#a29bfe]/30 text-xs"
            />
          </div>
          <button
            onClick={() => {
              if (!editKey) return;
              let parsedValue: unknown = editValue;
              try { parsedValue = JSON.parse(editValue); } catch { /* use as string */ }
              updateMut.mutate({ key: editKey, value: parsedValue });
            }}
            disabled={updateMut.isPending || !editKey}
            className="px-4 py-2 bg-gradient-to-r from-[#6c5ce7] to-[#a29bfe] hover:from-[#7c6df7] hover:to-[#b0abff] text-white rounded-md transition-all duration-150 font-medium flex items-center gap-1.5 text-xs"
          >
            <Save className="w-3.5 h-3.5" /> 保存
          </button>
        </div>
      </Card>
    </div></ErrorBoundary>
  );
}
