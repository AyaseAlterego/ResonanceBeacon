import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  GitBranch,
  Cpu,
  CheckSquare,
  Wrench,
  Settings,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/pipelines', label: 'Pipelines', icon: GitBranch },
  { to: '/agents', label: 'Agents', icon: Cpu },
  { to: '/approvals', label: 'Approvals', icon: CheckSquare },
  { to: '/config', label: 'Config', icon: Wrench },
];

export default function NavRail() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex flex-col items-center w-12 py-2 gap-1" style={{ backgroundColor: '#0d0d14' }}>
      <div className="flex flex-col items-center gap-1 flex-1">
        {navItems.map(({ to, label, icon: Icon }) => {
          const active = isActive(to);
          return (
            <button
              key={to}
              title={label}
              onClick={() => navigate(to)}
              className="flex items-center justify-center w-9 h-9 rounded-lg transition-colors"
              style={{
                backgroundColor: active ? '#6c5ce7/10' : undefined,
                color: active ? '#a29bfe' : '#6b7280',
              }}
              onMouseEnter={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = '#1f1f38';
                if (!active) e.currentTarget.style.color = '#d1d5db';
              }}
              onMouseLeave={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = 'transparent';
                if (!active) e.currentTarget.style.color = '#6b7280';
              }}
            >
              <Icon className="w-5 h-5" />
            </button>
          );
        })}
      </div>

      <div className="flex flex-col items-center gap-1 mt-auto">
        <button
          title="Settings"
          className="flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 hover:bg-[#1f1f38] hover:text-gray-300 transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
        <span className="text-[10px] text-gray-600">v0.1</span>
      </div>
    </div>
  );
}
