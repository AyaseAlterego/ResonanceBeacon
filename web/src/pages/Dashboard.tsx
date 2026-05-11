import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import { GitBranch, Bot, CheckSquare } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const healthQ = useQuery({ queryKey: ['health'], queryFn: api.health.check, refetchInterval: 10000 });
  const pipelinesQ = useQuery({ queryKey: ['pipelines'], queryFn: api.pipeline.list });
  const agentsQ = useQuery({ queryKey: ['agents'], queryFn: api.agent.list });
  const approvalsQ = useQuery({ queryKey: ['approvals-pending'], queryFn: api.approval.pending });

  const isLoading = pipelinesQ.isLoading || agentsQ.isLoading;
  const error = pipelinesQ.error?.message || agentsQ.error?.message;

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => { pipelinesQ.refetch(); agentsQ.refetch(); }} />;

  const pipelines = pipelinesQ.data?.流水线列表 ?? [];
  const agents = agentsQ.data?.智能体列表 ?? [];
  const pendingCount = approvalsQ.data?.总数 ?? 0;
  const running = pipelines.filter(p => p.状态 === 'running').length;
  const completed = pipelines.filter(p => p.状态 === 'completed').length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="流水线总数" value={pipelinesQ.data?.总数 ?? 0} sub={`${running} 运行中`} color="text-cyber-blue" />
        <StatCard label="智能体总数" value={agentsQ.data?.总数 ?? 0} sub="在线" color="text-cyber-green" />
        <StatCard label="待审批" value={pendingCount} color="text-cyber-yellow" />
        <StatCard label="系统状态" value={healthQ.data?.状态 ?? '—'} sub={healthQ.data?.版本} color="text-cyber-purple" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card
          title="最近流水线"
          action={
            <Link to="/pipelines" className="text-xs text-accent-400 hover:text-accent-300">
              查看全部
            </Link>
          }
        >
          {pipelines.length === 0 ? (
            <p className="text-sm text-dark-500 py-4 text-center">暂无流水线</p>
          ) : (
            <div className="space-y-2">
              {pipelines.slice(0, 5).map(p => (
                <Link
                  key={p.ID}
                  to={`/pipelines/${p.ID}`}
                  className="flex items-center justify-between p-3 rounded-md bg-dark-900/40 hover:bg-dark-800/60 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <GitBranch className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">{p.名称}</span>
                  </div>
                  <StatusBadge status={p.状态} />
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card
          title="智能体状态"
          action={
            <Link to="/agents" className="text-xs text-accent-400 hover:text-accent-300">
              查看全部
            </Link>
          }
        >
          {agents.length === 0 ? (
            <p className="text-sm text-dark-500 py-4 text-center">暂无智能体</p>
          ) : (
            <div className="space-y-2">
              {agents.map(a => (
                <Link
                  key={a.ID}
                  to="/agents"
                  className="flex items-center justify-between p-3 rounded-md bg-dark-900/40 hover:bg-dark-800/60 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Bot className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">{a.名称}</span>
                    <span className="text-xs text-dark-500">{a.类别}</span>
                  </div>
                  <StatusBadge status={a.状态} />
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>

      {pendingCount > 0 && (
        <Card
          title="待审批请求"
          action={
            <Link to="/approvals" className="text-xs text-cyber-yellow hover:text-yellow-300">
              {pendingCount} 项待处理
            </Link>
          }
        >
          <div className="flex items-center gap-3 p-3 rounded-md bg-yellow-900/10 border border-yellow-800/20">
            <CheckSquare className="w-4 h-4 text-cyber-yellow" />
            <span className="text-sm text-yellow-300">有 {pendingCount} 项审批请求等待处理</span>
          </div>
        </Card>
      )}

      <Card title="系统信息">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-dark-500 text-xs">服务</p>
            <p className="text-dark-200 font-mono">{healthQ.data?.服务 ?? '—'}</p>
          </div>
          <div>
            <p className="text-dark-500 text-xs">版本</p>
            <p className="text-dark-200 font-mono">{healthQ.data?.版本 ?? '—'}</p>
          </div>
          <div>
            <p className="text-dark-500 text-xs">运行流水线</p>
            <p className="text-dark-200 font-mono">{running}</p>
          </div>
          <div>
            <p className="text-dark-500 text-xs">已完成流水线</p>
            <p className="text-dark-200 font-mono">{completed}</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
