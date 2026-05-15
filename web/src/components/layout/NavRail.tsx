import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  GitBranch,
  Cpu,
  CheckSquare,
  Wrench,
  Settings,
} from 'lucide-react';

const navItems = [
  { to: '/', label: '仪表板', icon: LayoutDashboard },
  { to: '/projects', label: '项目', icon: FolderOpen },
  { to: '/pipelines', label: '流水线', icon: GitBranch },
  { to: '/agents', label: '智能体', icon: Cpu },
  { to: '/approvals', label: '审批', icon: CheckSquare },
  { to: '/config', label: '配置', icon: Wrench },
];

export default function NavRail() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex flex-col items-center w-12 py-2 gap-1 bg-[#0d0d14]">
      <div className="flex flex-col items-center gap-1 flex-1">
        {navItems.map(({ to, label, icon: Icon }) => {
          const active = isActive(to);
          return (
            <button
              key={to}
              title={label}
              onClick={() => navigate(to)}
              className={`flex items-center justify-center w-9 h-9 rounded-lg transition-colors ${
                active ? 'bg-[#6c5ce7]/10 text-[#a29bfe]' : 'text-[#6b7280] hover:bg-[#1f1f38] hover:text-[#d1d5db]'
              }`}
            >
              <Icon className="w-5 h-5" />
            </button>
          );
        })}
      </div>

      <div className="flex flex-col items-center gap-1 mt-auto">
        <button
          title="设置"
          onClick={() => navigate('/config')}
          className="flex items-center justify-center w-9 h-9 rounded-lg text-[#6b7280] hover:bg-[#1f1f38] hover:text-[#d1d5db] transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
        <span className="text-[10px] text-[#4b5563]">v0.1</span>
      </div>
    </div>
  );
}
