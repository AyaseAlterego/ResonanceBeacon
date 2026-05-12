import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { api } from '../../api/client'

interface Message {
  id: string
  role: 'hermes' | 'user'
  content: string
}

export default function HermesChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initializedRef = useRef(false)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true
    api.hermes.chat({ message: '你好' }).then(r => {
      setMessages([{ id: '0', role: 'hermes', content: r.reply }])
    }).catch(() => {
      setMessages([{ id: '0', role: 'hermes', content: '你好，我是 Hermes，你的元智能体助手。' }])
    })
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isTyping) return
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)
    try {
      const res = await api.hermes.chat({ message: input })
      const hermesMsg: Message = { id: (Date.now() + 1).toString(), role: 'hermes', content: res.reply }
      setMessages(prev => [...prev, hermesMsg])
    } catch {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: 'hermes', content: '抱歉，我暂时无法连接后端。' }])
    } finally {
      setIsTyping(false)
    }
  }

  const highlight = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <span key={i} className="text-[#a29bfe] font-medium">{part.slice(2, -2)}</span>
      }
      return <span key={i}>{part}</span>
    })
  }

  return (
    <div className="flex flex-col h-full bg-black/5">
      <div className="flex-1 overflow-y-auto p-[10px] flex flex-col gap-[8px]">
        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-[8px] max-w-[85%] ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
            <div className={`w-[24px] h-[24px] rounded-[6px] flex items-center justify-center text-[11px] shrink-0 mt-[2px] ${
              msg.role === 'hermes' ? 'bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe]' : 'bg-white/[0.06] border border-white/[0.06]'
            }`}>
              {msg.role === 'hermes' ? '✦' : '你'}
            </div>
            <div className={`p-[8px_10px] rounded-[8px] text-[11px] leading-[1.6] whitespace-pre-wrap ${
              msg.role === 'hermes' ? 'bg-[#6c5ce7]/[0.06] border border-[#6c5ce7]/[0.08] text-white/70' : 'bg-[#6c5ce7]/[0.12] border border-[#6c5ce7]/[0.15] text-white/80'
            }`}>
              {highlight(msg.content)}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-center gap-[3px] px-[10px] py-[6px] self-start ml-[32px]">
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" />
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.2s' }} />
            <span className="w-[5px] h-[5px] rounded-full bg-[#a29bfe]/50 animate-pulse" style={{ animationDelay: '0.4s' }} />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-[8px_10px] border-t border-[#6c5ce7]/[0.06] flex gap-[6px] bg-black/10">
        <input className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-[6px] px-[10px] py-[7px] text-[12px] text-white/60 outline-none placeholder:text-white/[0.1] focus:border-[#6c5ce7]/20"
          placeholder="向 Hermes 询问项目进度..."
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} disabled={isTyping || !input.trim()}
          className="w-[30px] h-[30px] rounded-[6px] bg-gradient-to-br from-[#6c5ce7] to-[#a29bfe] text-white flex items-center justify-center hover:shadow-[0_3px_10px_rgba(108,92,231,0.3)] disabled:opacity-50 shrink-0">
          <Send size={14} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  )
}