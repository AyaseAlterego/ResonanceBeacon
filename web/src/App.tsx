import { useEffect } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './components/theme-provider';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Pipelines from './pages/Pipelines';
import PipelineDetail from './pages/PipelineDetail';
import Agents from './pages/Agents';
import Approvals from './pages/Approvals';
import Config from './pages/Config';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8765';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5000,
    },
  },
});

function AutoSetup() {
  useEffect(() => {
    if (localStorage.getItem('hermes_api_key')) return;
    fetch(`${API_BASE}/设置/默认密钥`, { signal: AbortSignal.timeout(3000) })
      .then(r => r.json())
      .then(data => {
        if (data?.密钥) {
          localStorage.setItem('hermes_api_key', data.密钥);
          window.location.reload();
        }
      })
      .catch(() => {
        // Fallback: use hardcoded dev key
        localStorage.setItem('hermes_api_key', 'hermes-local-dev-key');
        window.location.reload();
      });
  }, []);
  return null;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <HashRouter>
            <AutoSetup />
            <Routes>
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/projects" element={<Projects />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/pipelines" element={<Pipelines />} />
                <Route path="/pipelines/:id" element={<PipelineDetail />} />
                <Route path="/agents" element={<Agents />} />
                <Route path="/approvals" element={<Approvals />} />
                <Route path="/config" element={<Config />} />
              </Route>
            </Routes>
          </HashRouter>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
