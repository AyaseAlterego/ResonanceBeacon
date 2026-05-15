import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import Loading from '../components/Loading';
import ErrorBoundary from '../components/ErrorBoundary';
import { Send, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import type { ConversationMessage, Artifact, ProjectStage, SuperpowersSkill } from '../types';

const 阶段顺序: ProjectStage[] = ['需求分析', '架构设计', '方案确认', '开发执行', '代码审查', '完成'];

const 阶段技能名: Record<string, string> = {
  '需求分析': 'brainstorming',
  '架构设计': 'writing-plans',
  '方案确认': 'human-gate',
  '开发执行': 'subagent-driven-dev',
  '代码审查': 'code-review',
  '完成': 'finishing',
};

const 制品图标: Record<string, string> = {
  spec: '📋',
  plan: '📝',
  code: '💻',
  review: '🔍',
};

export default function ProjectDetail() {
  const id = window.location.hash.match(/#\/projects\/([^/]+)/)?.[1] || '';
  const qc = useQueryClient();

  const projectQ = useQuery({ queryKey: ['project', id], queryFn: () => api.project.get(id) });
  const conversationQ = useQuery({ queryKey: ['conversation', id], queryFn: () => api.project.conversation.get(id), enabled: !!id });
  const artifactsQ = useQuery({ queryKey: ['artifacts', id], queryFn: () => api.project.artifacts.list(id), enabled: !!id });

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [pendingArtifact, setPendingArtifact] = useState<Artifact | null>(null);
  const [expandedArtifact, setExpandedArtifact] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationQ.data, isTyping]);

  const sendMut = useMutation({
    mutationFn: (内容: string) => api.project.conversation.sendMessage(id, 内容),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['conversation', id] });
      qc.invalidateQueries({ queryKey: ['artifacts', id] });
      if (res.阶段产出) {
        setPendingArtifact(res.阶段产出);
      }
    },
    onSettled: () => setIsTyping(false),
  });

  const confirmMut = useMutation({
    mutationFn: () => api.project.confirm(id, '确认'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', id] });
      qc.invalidateQueries({ queryKey: ['conversation', id] });
      setPendingArtifact(null);
    },
  });

  const rejectMut = useMutation({
    mutationFn: (反馈: string) => api.project.reject(id, 反馈),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', id] });
      qc.invalidateQueries({ queryKey: ['conversation', id] });
      setPendingArtifact(null);
    },
  });

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    setIsTyping(true);
    sendMut.mutate(input.trim());
    setInput('');
  };

  if (projectQ.isLoading) return <Loading />;

  const project = projectQ.data;
  if (!project) return <div className="text-dark-500 text-sm">项目不存在</div>;

  const messages = conversationQ.data?.消息列表 ?? [];
  const artifacts = artifactsQ.data?.制品列表 ?? [];
  const currentStageIdx = 阶段顺序.indexOf(project.阶段 as ProjectStage);

  const highlight = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <span key={i} className="text-[#a29bfe] font-medium">{part.slice(2, -2)}</span>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <ErrorBoundary><div className="flex h-[calc(100vh-38px)] -m-6">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.04]">
          <div>
            <h2 className="text-sm font-semibold text-dark-100">{project.名称}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-dark-500 font-mono">{project.ID}</span>
              <span className="text-[10px] text-[#a29bfe]">·</span>
              <span className="text-[10px] text-[#a29bfe]">{阶段技能名[project.阶段] || project.阶段}</span>
            </div>
          </div>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full bg-white/[0.03] border border-white/[0.06] ${
            project.阶段 === '完成' ? 'text-emerald-400' : project.阶段 === '失败' ? 'text-red-400' : 'text-[#a29bfe]'
          }`}>
            {project.阶段}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map(msg => (
            <div key={msg.ID} className={`flex gap-2 max-w-[85%] ${msg.角色 === 'user' ? 'self-end flex-row-reverse ml-auto' : 'self-start'}`}>
              <div className={`w-6 h-6 rounded-md flex items-center justify-center text-[10px] shrink-0 mt-0.5 ${
                msg.角色 === 'hermes' ? 'bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe]' :
                msg.角色 === 'system' ? 'bg-amber-500/20 text-amber-400' :
                'bg-white/[0.06] border border-white/[0.06]'
              }`}>
                {msg.角色 === 'hermes' ? '✦' : msg.角色 === 'system' ? '⚡' : '你'}
              </div>
              <div className={`p-2.5 rounded-lg text-[12px] leading-relaxed whitespace-pre-wrap ${
                msg.角色 === 'hermes' ? 'bg-[#6c5ce7]/[0.06] border border-[#6c5ce7]/[0.08] text-white/70' :
                msg.角色 === 'system' ? 'bg-amber-500/[0.06] border border-amber-500/[0.1] text-amber-200/70' :
                'bg-[#6c5ce7]/[0.12] border border-[#6c5ce7]/[0.15] text-white/80'
              }`}>
                {highlight(msg.内容)}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex items-center gap-1 px-3 py-2 self-start ml-8">
              <span className="w-1.5 h-1.5 rounded-full bg-[#a29bfe]/50 animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.2s' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {pendingArtifact && (
          <div className="border-t border-amber-500/20 bg-amber-500/[0.03] p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm">{制品图标[pendingArtifact.制品类型] || '📄'}</span>
              <span className="text-xs font-medium text-amber-300">{pendingArtifact.名称} 已生成</span>
              <span className="text-[10px] text-dark-500">({pendingArtifact.技能})</span>
            </div>
            <div className="bg-black/30 rounded-lg p-3 mb-3 max-h-40 overflow-y-auto">
              <pre className="text-[11px] text-white/60 whitespace-pre-wrap font-mono">{pendingArtifact.内容.slice(0, 1500)}{pendingArtifact.内容.length > 1500 ? '...' : ''}</pre>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => rejectMut.mutate('需要修改')}
                className="text-xs py-1.5 px-3 rounded-lg border border-white/[0.06] text-dark-400 hover:text-dark-200">
                继续修改
              </button>
              <button onClick={() => confirmMut.mutate()}
                disabled={confirmMut.isPending}
                className="text-xs py-1.5 px-3 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white disabled:opacity-50">
                {confirmMut.isPending ? '处理中...' : '确认并进入下一阶段'}
              </button>
            </div>
          </div>
        )}

        {!pendingArtifact && project.阶段 !== '完成' && project.阶段 !== '已取消' && project.阶段 !== '失败' && (
          <div className="p-3 border-t border-white/[0.04] flex gap-2 bg-black/5">
            <input className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-xs text-white/60 outline-none placeholder:text-white/[0.1] focus:border-[#6c5ce7]/20"
              placeholder="输入消息与 Hermes 对话..."
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend} disabled={isTyping || !input.trim()}
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white flex items-center justify-center hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] disabled:opacity-50 shrink-0">
              <Send size={14} strokeWidth={2.5} />
            </button>
          </div>
        )}
      </div>

      <div className="w-[260px] border-l border-white/[0.04] bg-[#0d0d14] flex flex-col overflow-y-auto">
        <div className="p-4">
          <h3 className="text-xs font-medium text-dark-400 mb-3">技能进度</h3>
          <div className="space-y-2">
            {阶段顺序.map((阶段, idx) => {
              const isDone = idx < currentStageIdx;
              const isCurrent = idx === currentStageIdx;
              return (
                <div key={阶段} className={`flex items-center gap-2 text-[11px] ${
                  isDone ? 'text-emerald-400' : isCurrent ? 'text-[#a29bfe]' : 'text-dark-500'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    isDone ? 'bg-emerald-400' : isCurrent ? 'bg-[#a29bfe]' : 'bg-dark-600'
                  }`} />
                  <span>{阶段}</span>
                  {isCurrent && <span className="text-[9px] text-dark-500 ml-auto">{阶段技能名[阶段]}</span>}
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-4 border-t border-white/[0.04]">
          <h3 className="text-xs font-medium text-dark-400 mb-3">制品</h3>
          {artifacts.length === 0 ? (
            <p className="text-[11px] text-dark-600">暂无制品</p>
          ) : (
            <div className="space-y-2">
              {artifacts.map(a => (
                <div key={a.ID}>
                  <button onClick={() => setExpandedArtifact(expandedArtifact === a.ID ? null : a.ID)}
                    className="w-full flex items-center gap-2 text-left p-2 rounded-md bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                    <span className="text-xs">{制品图标[a.制品类型] || '📄'}</span>
                    <span className="text-[11px] text-dark-200 flex-1 truncate">{a.名称}</span>
                    {expandedArtifact === a.ID ? <ChevronUp className="w-3 h-3 text-dark-500" /> : <ChevronDown className="w-3 h-3 text-dark-500" />}
                  </button>
                  {expandedArtifact === a.ID && (
                    <div className="mt-1 p-2 bg-black/30 rounded-md max-h-48 overflow-y-auto">
                      <pre className="text-[10px] text-white/50 whitespace-pre-wrap font-mono">{a.content.slice(0, 2000)}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div></ErrorBoundary>
  );
}
