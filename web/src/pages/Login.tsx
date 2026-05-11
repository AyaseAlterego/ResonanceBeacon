import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Activity, KeyRound } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;
    setLoading(true);
    setError('');
    const ok = await login(key.trim());
    setLoading(false);
    if (!ok) {
      setError('API Key 无效或服务不可用');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Activity className="w-10 h-10 text-cyber-blue mx-auto mb-3" />
          <h1 className="text-xl font-semibold glow-text tracking-wide">起源信标</h1>
          <p className="text-sm text-dark-400 mt-1">请输入 API Key 以继续</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-xs font-medium text-dark-300 mb-1.5">
              <KeyRound className="w-3.5 h-3.5 inline mr-1" />
              API Key
            </label>
            <input
              type="password"
              value={key}
              onChange={e => setKey(e.target.value)}
              placeholder="输入您的 API Key"
              className="input"
              autoFocus
              disabled={loading}
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !key.trim()}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '验证中...' : '登录'}
          </button>
        </form>
      </div>
    </div>
  );
}
