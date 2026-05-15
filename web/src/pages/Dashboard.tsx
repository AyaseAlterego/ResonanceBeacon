import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import Loading from '../components/Loading';
import ErrorBoundary from '../components/ErrorBoundary';
import { GitBranch, Bot, CheckSquare, FolderOpen, Rocket, AlertCircle, LayoutKanban, Cpu, Play, Pause } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    api.health.check()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  const healthQ = useQuery({ queryKey: ['health'], queryFn: api.health.check, refetchInterval: 10000, enabled: backendOnline === true });
  const projectsQ = useQuery({ queryKey: ['projects'], queryFn: api.project.list, enabled: backendOnline === true });
  const pipelinesQ = useQuery({ queryKey: ['pipelines'], queryFn: api.pipeline.list, enabled: backendOnline === true });
  const agentsQ = useQuery({ queryKey: ['agents'], queryFn: api.agent.list, enabled: backendOnline === true });
  const approvalsQ = useQuery({ queryKey: ['approvals-pending'], queryFn: api.approval.pending, enabled: backendOnline === true });

  if (backendOnline === null) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-[#6c5ce7] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-[#6b7280]">正在连接后端服务...</p>
        </div>
      </div>
    );
  }

  if (!backendOnline) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="max-w-md text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] flex items-center justify-center mx-auto shadow-lg shadow-[#6c5ce7]/20">
            <Rocket className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white/80">起源信标</h1>
          <p className="text-sm text-[#6b7280] leading-relaxed">
            智能流水线开发系统 · Oh My Hermes 编排层
          </p>
          <div className="bg-[#1a1a2e]/60 border border-[#6c5ce7]/10 rounded-xl p-5 text-left space-y-3">
            <div className="flex items-center gap-2 text-sm text-[#f59e0b]">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium">后端服务未运行</span>
            </div>
            <p className="text-xs text-[#6b7280] leading-relaxed">
              请确认 Python 后端已启动。运行以下命令：
            </p>
            <div className="bg-black/40 rounded-lg p-3 font-mono text-xs text-[#a29bfe] select-all">
              cd C:\Ai\起源信标\ResonanceBeacon<br />
              python -m uvicorn hermes.接口.应用:应用 --host 127.0.0.1 --port 8765
            </div>
            <button
              onClick={() => window.location.reload()}
              className="w-full py-2 rounded-lg bg-gradient-to-r from-[#6c5ce7] to-[#a29bfe] text-white text-sm font-medium hover:shadow-lg hover:shadow-[#6c5ce7]/20 transition-all"
            >
              重试连接
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isLoading = projectsQ.isLoading || pipelinesQ.isLoading || agentsQ.isLoading;
  const projects = projectsQ.data?.项目列表 ?? [];
  const pipelines = pipelinesQ.data?.流水线列表 ?? [];
  const agents = agentsQ.data?.智能体列表 ?? [];
  const pendingCount = approvalsQ.data?.总数 ?? 0;
  const running = pipelines.filter(p => p.状态 === 'running').length;
  const completed = pipelines.filter(p => p.状态 === 'completed').length;

  if (isLoading) return <Loading />;

  return (
    <ErrorBoundary><div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white/80">运行总览</h1>
        <div className="flex gap-2">
          <Link to="/projects" className="px-4 py-2 rounded-lg bg-[#1a1a2e]/60 border border-white/10 text-white text-sm font-medium hover:bg-[#1a1a2e] transition-all flex items-center gap-2">
            <FolderOpen className="w-4 h-4" /> 项目管理
          </Link>
          <Link to="/projects/new" className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#6c5ce7] to-[#a29bfe] text-white text-sm font-medium hover:shadow-lg hover:shadow-[#6c5ce7]/20 transition-all flex items-center gap-2">
            <Rocket className="w-4 h-4" /> 新建项目
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="活跃项目" value={projects.length} sub="项目" color="text-[#a29bfe]" />
        <StatCard label="运行中" value={running} sub="流水线" color="text-[#54a0ff]" />
        <StatCard label="智能体" value={agentsQ.data?.总数 ?? 0} sub="在线" color="text-[#28c840]" />
        <StatCard label="待审批" value={pendingCount} color="text-[#f59e0b]" />
        <StatCard label="已完成" value={completed} sub="流水线" color="text-[#28c840]" />
      </div>

      {/* 自主循环状态 */}
      <Card title="自主循环引擎">
        <div className="flex items-center justify-between p-3 rounded-md bg-black/20">
          <div className="flex items-center gap-3">
            <Cpu className="w-5 h-5 text-[#a29bfe]" />
            <div>
              <div className="text-sm text-white/60">Oh My Hermes CTO Loop</div>
              <div className="text-xs text-[#6b7280]">每小时自动分诊 → 开发 → 审查 → 审批</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#28c840]">运行中</span>
            <button className="p-1 rounded hover:bg-white/10">
              <Pause className="w-4 h-4 text-[#6b7280]" />
            </button>
          </div>
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* 项目列表 */}
        <Card title="最近项目" action={<Link to="/projects" className="text-xs text-[#a29bfe] hover:text-[#c4b5fd]">查看全部</Link>}>
          {projects.length === 0 ? (
            <div className="text-center py-8 text-sm text-[#6b7280]">
              暂无项目，点击「新建项目」开始
            </div>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 5).map(p => (
                <Link key={p.ID} to={`/projects/${p.ID}`}
                  className="flex items-center justify-between p-3 rounded-md bg-black/20 hover:bg-[#1a1a2e]/60 transition-colors">
                  <div className="flex items-center gap-3">
                    <FolderOpen className="w-4 h-4 text-[#6b7280]" />
                    <span className="text-sm text-white/60">{p.名称}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/projects/${p.ID}/kanban`}
                      className="p-1 rounded hover:bg-white/10"
                      onClick={e => e.stopPropagation()}
                    >
                      <LayoutKanban className="w-4 h-4 text-[#6b7280] hover:text-[#a29bfe]" />
                    </Link>
                    <span className="text-xs text-[#a29bfe]">{p.阶段}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>

        {/* 智能体状态 */}
        <Card title="智能体状态" action={<Link to="/agents" className="text-xs text-[#a29bfe] hover:text-[#c4b5fd]">查看全部</Link>}>
          {agents.length === 0 ? (
            <div className="text-center py-8 text-sm text-[#6b7280]">
              暂无智能体
            </div>
          ) : (
            <div className="space-y-2">
              {agents.map(a => (
                <Link key={a.ID} to="/agents"
                  className="flex items-center justify-between p-3 rounded-md bg-black/20 hover:bg-[#1a1a2e]/60 transition-colors">
                  <div className="flex items-center gap-3">
                    <Bot className="w-4 h-4 text-[#6b7280]" />
                    <span className="text-sm text-white/60">{a.名称}</span>
                    <span className="text-xs text-[#6b7280]">{a.类别}</span>
                  </div>
                  <StatusBadge status={a.状态} />
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>

      {pendingCount > 0 && (
        <Card title="待审批请求" action={<Link to="/approvals" className="text-xs text-[#f59e0b]">{pendingCount} 项待处理</Link>}>
          <div className="flex items-center gap-3 p-3 rounded-md bg-[#f59e0b]/5 border border-[#f59e0b]/10">
            <CheckSquare className="w-4 h-4 text-[#f59e0b]" />
            <span className="text-sm text-[#fbbf24]">有 {pendingCount} 项审批请求等待处理</span>
          </div>
        </Card>
      )}
    </div></ErrorBoundary>
  );
}
