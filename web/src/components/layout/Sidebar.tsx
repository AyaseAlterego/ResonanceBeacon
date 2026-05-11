const mockPipelines = [
  { name: '数据采集流水线', status: 'running', progress: 72 },
  { name: '模型训练流程', status: 'running', progress: 45 },
  { name: '内容审核管线', status: 'idle', progress: 100 },
  { name: '日志分析任务', status: 'running', progress: 88 },
  { name: '数据同步作业', status: 'failed', progress: 34 },
];

const mockAgents = [
  { name: 'Hermes', role: '协调智能体', status: 'online' },
  { name: 'Athena', role: '分析智能体', status: 'online' },
  { name: 'Prometheus', role: '执行智能体', status: 'offline' },
];

const statusTagClass = (status: string) => {
  switch (status) {
    case 'running':
    case 'online':
      return 'bg-green-900/40 text-green-400 border border-green-800/30';
    case 'idle':
      return 'bg-yellow-900/40 text-yellow-400 border border-yellow-800/30';
    case 'failed':
    case 'offline':
      return 'bg-red-900/40 text-red-400 border border-red-800/30';
    default:
      return 'bg-dark-700/40 text-dark-300 border border-dark-600/30';
  }
};

const statusLabel = (status: string) => {
  switch (status) {
    case 'running': return '运行中';
    case 'idle': return '空闲';
    case 'failed': return '失败';
    case 'online': return '在线';
    case 'offline': return '离线';
    default: return status;
  }
};

export default function Sidebar() {
  const runningCount = mockPipelines.filter(p => p.status === 'running').length;
  const onlineCount = mockAgents.filter(a => a.status === 'online').length;

  return (
    <div className="w-[200px] flex flex-col overflow-y-auto border-r border-white/5" style={{ backgroundColor: '#0d0d14' }}>
      <div className="p-3">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-gray-400 tracking-wide">活动流水线</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-900/40 text-purple-400 border border-purple-800/30">
            {runningCount}
          </span>
        </div>
        <div className="space-y-2">
          {mockPipelines.map((p) => (
            <div key={p.name} className="group cursor-pointer">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs text-gray-300 truncate max-w-[110px]">{p.name}</span>
                <span className={`text-[9px] px-1 py-0.5 rounded ${statusTagClass(p.status)}`}>
                  {statusLabel(p.status)}
                </span>
              </div>
              <div className="w-full h-1 rounded-full bg-white/5">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${p.progress}%`,
                    backgroundColor: p.status === 'failed' ? '#ef4444' : '#a29bfe',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/5 mx-3" />

      <div className="p-3">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-gray-400 tracking-wide">智能体状态</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-900/40 text-green-400 border border-green-800/30">
            {onlineCount}
          </span>
        </div>
        <div className="space-y-2">
          {mockAgents.map((a) => (
            <div key={a.name} className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-xs text-gray-300">{a.name}</span>
                <span className="text-[10px] text-gray-500">{a.role}</span>
              </div>
              <span className={`text-[9px] px-1 py-0.5 rounded ${statusTagClass(a.status)}`}>
                {statusLabel(a.status)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
