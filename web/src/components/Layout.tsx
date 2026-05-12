import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import TitleBar from './layout/TitleBar';
import NavRail from './layout/NavRail';
import Sidebar from './layout/Sidebar';
import HermesChat from './layout/HermesChat';

export default function Layout() {
  const [pythonConnected, setPythonConnected] = useState(true);

  useEffect(() => {
    if (window.electronAPI?.onPythonStatusChange) {
      window.electronAPI.onPythonStatusChange((data) => {
        setPythonConnected(data.status === 'connected');
      });
    }
  }, []);

  const handleMinimize = () => {
    if (window.electronAPI?.minimizeWindow) window.electronAPI.minimizeWindow();
  };

  const handleMaximize = () => {
    if (window.electronAPI?.maximizeWindow) window.electronAPI.maximizeWindow();
  };

  const handleClose = () => {
    if (window.electronAPI?.closeWindow) window.electronAPI.closeWindow();
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ backgroundColor: '#0a0a0f' }}>
      <TitleBar
        onMinimize={handleMinimize}
        onMaximize={handleMaximize}
        onClose={handleClose}
        pythonConnected={pythonConnected}
      />

      <div className="flex flex-1 overflow-hidden">
        <NavRail />
        <Sidebar />

        <main className="flex-1 overflow-auto p-6 animate-fadeIn">
          <Outlet />
        </main>

        <div className="w-[300px] border-l border-white/5 flex flex-col" style={{ backgroundColor: '#0d0d14' }}>
          <HermesChat />
        </div>
      </div>
    </div>
  );
}
