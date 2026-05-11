import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-dark-100">配置管理</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-dark-500">来源: {configQ.data?.来源}</span>
          <button onClick={() => configQ.refetch()} className="text-dark-400 hover:text-dark-200">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex gap-1 bg-dark-800/60 rounded-md p-0.5 w-fit">
        <button
          onClick={() => setTab('current')}
          className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            tab === 'current' ? 'bg-accent-700/60 text-white' : 'text-dark-400 hover:text-dark-200'
          }`}
        >
          当前配置
        </button>
        <button
          onClick={() => setTab('merged')}
          className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            tab === 'merged' ? 'bg-accent-700/60 text-white' : 'text-dark-400 hover:text-dark-200'
          }`}
        >
          合并后配置
        </button>
      </div>

      <Card title="配置内容" action={<Settings className="w-4 h-4 text-dark-500" />}>
        <div className="space-y-4">
          {Object.entries(config).map(([section, value]) => (
            <div key={section}>
              <h4 className="text-xs font-semibold text-accent-400 mb-2 uppercase tracking-wider">{section}</h4>
              <div className="bg-dark-900/60 rounded-md p-3 font-mono text-xs text-dark-300 space-y-1">
                {typeof value === 'object' && value !== null
                  ? Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-2">
                        <span className="text-dark-500">{k}:</span>
                        <span className="text-dark-200">
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
            <label className="text-xs text-dark-400 mb-1 block">键路径</label>
            <input
              type="text"
              value={editKey}
              onChange={e => setEditKey(e.target.value)}
              placeholder="例: 流水线.默认超时"
              className="input text-xs"
            />
          </div>
          <div>
            <label className="text-xs text-dark-400 mb-1 block">值</label>
            <input
              type="text"
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              placeholder="例: 600"
              className="input text-xs"
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
            className="btn-primary flex items-center gap-1.5 text-xs"
          >
            <Save className="w-3.5 h-3.5" /> 保存
          </button>
        </div>
      </Card>
    </div>
  );
}
