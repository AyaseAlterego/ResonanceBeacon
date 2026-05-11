import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import { Bot, Heart, Gauge } from 'lucide-react';

export default function Agents() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ['agents'], queryFn: api.agent.list, refetchInterval: 15000 });

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay message={error.message} onRetry={() => refetch()} />;

  const agents = data?.智能体列表 ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-dark-100">智能体列表</h2>
        <span className="text-xs text-dark-400">共 {data?.总数 ?? 0} 个</span>
      </div>

      {agents.length === 0 ? (
        <Card>
          <p className="text-sm text-dark-500 text-center py-8">暂无智能体</p>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(a => (
            <AgentCard key={a.ID} agent={a} />
          ))}
        </div>
      )}
    </div>
  );
}

function AgentCard({ agent }: { agent: { ID: string; 名称: string; 类别: string; 状态: string; 负载: number } }) {
  const healthQ = useQuery({
    queryKey: ['agent-health', agent.ID],
    queryFn: () => api.agent.health(agent.ID),
    refetchInterval: 30000,
  });
  const loadQ = useQuery({
    queryKey: ['agent-load', agent.ID],
    queryFn: () => api.agent.load(agent.ID),
    refetchInterval: 15000,
  });

  const categoryLabels: Record<string, string> = {
    ultrabrain: '超级大脑',
    deep: '深度推理',
    specialist: '专家',
    unknown: '未知',
  };

  const loadData = loadQ.data;
  const loadPercent = loadData ? Math.round(loadData.负载率 * 100) : Math.round(agent.负载 * 100);

  return (
    <div className="card-hover">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-accent-400" />
          <span className="text-sm font-medium text-dark-100">{agent.名称}</span>
        </div>
        <StatusBadge status={agent.状态} />
      </div>

      <div className="space-y-3 text-xs">
        <div className="flex items-center justify-between text-dark-400">
          <span>ID</span>
          <span className="font-mono text-dark-300">{agent.ID}</span>
        </div>
        <div className="flex items-center justify-between text-dark-400">
          <span>类别</span>
          <span className="text-dark-300">{categoryLabels[agent.类别] ?? agent.类别}</span>
        </div>

        <div className="pt-2 border-t border-dark-700/30">
          <div className="flex items-center gap-2 text-dark-400 mb-2">
            <Heart className="w-3.5 h-3.5" />
            <span>健康检查</span>
            <span className={healthQ.data?.健康 ? 'text-green-400' : 'text-red-400'}>
              {healthQ.isLoading ? '检查中...' : healthQ.data?.健康 ? '正常' : '异常'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-dark-400">
            <Gauge className="w-3.5 h-3.5" />
            <span>负载</span>
            <div className="flex-1 h-1.5 bg-dark-700 rounded-full overflow-hidden ml-1">
              <div
                className={`h-full rounded-full transition-all ${loadPercent > 80 ? 'bg-cyber-red' : loadPercent > 50 ? 'bg-cyber-yellow' : 'bg-cyber-green'}`}
                style={{ width: `${loadPercent}%` }}
              />
            </div>
            <span className="font-mono text-dark-300 w-10 text-right">
              {loadData ? `${loadData.当前并发}/${loadData.最大并发}` : `${loadPercent}%`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
