import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

const tagClass = (status: string) => {
  switch (status) {
    case 'running': return 'bg-[#54a0ff]/10 text-[#54a0ff]'
    case 'completed': return 'bg-[#28c840]/10 text-[#28c840]'
    case 'failed': return 'bg-[#ff5f57]/10 text-[#ff5f57]'
    case 'cancelled': return 'bg-white/5 text-white/30'
    default: return 'bg-[#f59e0b]/10 text-[#f59e0b]'
  }
}

const statusLabel = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return '待开始'
  }
}

export default function Sidebar() {
  const pipelinesQ = useQuery({ queryKey: ['pipelines'], queryFn: api.pipeline.list, refetchInterval: 10000 })
  const agentsQ = useQuery({ queryKey: ['agents'], queryFn: api.agent.list, refetchInterval: 10000 })

  const pipelines = pipelinesQ.data?.流水线列表 ?? []
  const agents = agentsQ.data?.智能体列表 ?? []
  const runningCount = pipelines.filter(p => p.状态 === 'running').length

  return (
    <div className="w-[200px] bg-black/10 border-r border-[#6c5ce7]/[0.06] flex flex-col shrink-0">
      <div className="px-[14px] pt-[14px] pb-[8px] flex items-center justify-between">
        <span className="text-[10px] font-semibold text-white/20 tracking-[1px]">流水线</span>
        <span className="text-[10px] text-white/10 bg-white/[0.03] px-[5px] rounded-[3px]">
          {runningCount > 0 ? `${runningCount} 运行中` : pipelines.length}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto px-2">
        {pipelines.length === 0 ? (
          <p className="text-[10px] text-white/10 text-center pt-6">暂无流水线</p>
        ) : (
          pipelines.slice(0, 8).map(p => (
            <div key={p.ID} className="px-[10px] py-[6px] rounded-[6px] mb-[2px] border border-transparent">
              <div className="text-[12px] text-white/65 font-medium mb-[1px] truncate">{p.名称}</div>
              <span className={`text-[9px] px-[5px] rounded-[3px] ${tagClass(p.状态)}`}>{statusLabel(p.状态)}</span>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-[#6c5ce7]/[0.06] px-[14px] py-[8px] shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[9px] font-semibold text-white/20 tracking-[1px]">智能体</span>
          <span className="text-[9px] text-[#6c5ce7]/40">{agents.length} 个</span>
        </div>
        {agents.length === 0 ? (
          <p className="text-[9px] text-white/10 text-center">暂无智能体</p>
        ) : (
          agents.slice(0, 5).map(a => (
            <div key={a.ID} className="flex items-center px-[6px] py-[3px] rounded-[4px] mb-[2px]">
              <div className={`w-[6px] h-[6px] rounded-full mr-[8px] shrink-0 ${
                a.状态 !== 'offline' ? 'bg-[#28c840] shadow-[0_0_6px_rgba(40,200,64,0.3)]' : 'bg-white/[0.1]'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="text-[11px] text-white/55 font-medium truncate">{a.名称}</div>
              </div>
              <span className={`text-[8px] px-[3px] rounded-[2px] ${tagClass(a.状态)}`}>{statusLabel(a.状态)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}