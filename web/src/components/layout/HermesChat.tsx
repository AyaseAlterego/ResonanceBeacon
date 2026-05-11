import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface Message {
  role: 'hermes' | 'user';
  content: string;
}

function parseBold(text: string) {
  const parts: ({ text: string; bold: boolean } | string)[] = [];
  const regex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push({ text: match[1], bold: true });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export default function HermesChat() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'hermes',
    content: '你好！我是 **Hermes**，你的智能开发助手。当前项目 **起源信标** 正在稳定运行中，版本 0.1.0。有什么我可以帮助你的吗？',
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: 'user', content: trimmed };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE || '';
      const res = await fetch(`${API_BASE}/智能体/hermes/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      const hermesMsg: Message = { role: 'hermes', content: data.reply };
      setMessages(prev => [...prev, hermesMsg]);
    } catch {
      setMessages(prev => [...prev, { role: 'hermes', content: '抱歉，我暂时无法连接后端' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex items-center gap-4 px-4 h-10 border-b border-white/5 shrink-0">
        <span className="text-xs text-gray-500 cursor-default select-none">日志</span>
        <span className="text-xs font-medium text-purple-400 cursor-default select-none border-b-2 border-purple-500 pb-[10px] -mb-px">
          Hermes 对话
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 scrollbar-thin">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
              msg.role === 'hermes'
                ? 'bg-purple-600/20 text-purple-400'
                : 'bg-gray-600/30 text-gray-400'
            }`}>
              {msg.role === 'hermes' ? '✦' : '你'}
            </div>

            {/* Bubble */}
            <div
              className={`max-w-[220px] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                msg.role === 'hermes'
                  ? 'border border-purple-500/10'
                  : 'border border-purple-500/20'
              }`}
              style={{
                backgroundColor: msg.role === 'hermes' ? 'rgba(108,92,231,0.06)' : 'rgba(108,92,231,0.12)',
              }}
            >
              {parseBold(msg.content).map((part, j) =>
                typeof part === 'string' ? (
                  <span key={j} className="text-gray-300">{part}</span>
                ) : (
                  <span key={j} className="text-purple-400 font-semibold">{part.text}</span>
                )
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 bg-purple-600/20 text-purple-400 text-[10px] font-bold">
              ✦
            </div>
            <div
              className="rounded-lg px-3 py-2 border border-purple-500/10 flex items-center gap-1"
              style={{ backgroundColor: 'rgba(108,92,231,0.06)' }}
            >
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-white/5 px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-200 placeholder-gray-600 outline-none focus:border-purple-500/40 transition-colors"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="w-7 h-7 rounded-lg flex items-center justify-center bg-purple-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-500 transition-colors shrink-0"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
