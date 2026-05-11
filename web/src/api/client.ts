import type {
  PipelineListResponse,
  Pipeline,
  PipelineCreateRequest,
  PipelineRunRequest,
  AgentListResponse,
  Agent,
  AgentHealthResponse,
  AgentLoadResponse,
  Approval,
  PendingApprovalsResponse,
  ApprovalDecisionRequest,
  ApprovalHistoryResponse,
  PipelineStagesResponse,
  PipelineArtifactsResponse,
  ConfigResponse,
  HealthResponse,
  ReadyResponse,
  HermesChatRequest,
  HermesChatResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8765';

function getApiKey(): string | null {
  return localStorage.getItem('hermes_api_key');
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const apiKey = getApiKey();
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (apiKey) {
    defaultHeaders['Authorization'] = `Bearer ${apiKey}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options?.headers as Record<string, string>,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('hermes_api_key');
    window.location.href = '/login';
    throw new Error('未授权，请重新登录');
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API 错误 ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  pipeline: {
    list: () => request<PipelineListResponse>('/流水线/'),
    get: (id: string) => request<Pipeline>(`/流水线/${id}`),
    create: (data: PipelineCreateRequest) =>
      request<Pipeline>('/流水线/', { method: 'POST', body: JSON.stringify(data) }),
    run: (id: string, data?: PipelineRunRequest) =>
      request<Record<string, string>>(`/流水线/${id}/运行`, { method: 'POST', body: JSON.stringify(data ?? { 流水线ID: id }) }),
    cancel: (id: string) =>
      request<Record<string, string>>(`/流水线/${id}/取消`, { method: 'POST' }),
    stages: (id: string) =>
      request<PipelineStagesResponse>(`/流水线/${id}/阶段`),
    artifacts: (id: string) =>
      request<PipelineArtifactsResponse>(`/流水线/${id}/制品`),
  },
  agent: {
    list: () => request<AgentListResponse>('/智能体/'),
    get: (id: string) => request<Agent>(`/智能体/${id}`),
    health: (id: string) => request<AgentHealthResponse>(`/智能体/${id}/健康检查`),
    load: (id: string) => request<AgentLoadResponse>(`/智能体/${id}/负载`),
  },
  approval: {
    pending: () => request<PendingApprovalsResponse>('/审批/待处理'),
    get: (id: string) => request<Approval>(`/审批/${id}`),
    decide: (id: string, data: ApprovalDecisionRequest) =>
      request<Record<string, string>>(`/审批/${id}/决策`, { method: 'POST', body: JSON.stringify(data) }),
    history: () => request<ApprovalHistoryResponse>('/审批/历史'),
  },
  config: {
    get: () => request<ConfigResponse>('/配置/'),
    merged: () => request<ConfigResponse>('/配置/合并后'),
    update: (keyPath: string, value: unknown) =>
      request<Record<string, string>>(`/配置/${keyPath}`, { method: 'PUT', body: JSON.stringify(value) }),
  },
  health: {
    check: () => request<HealthResponse>('/健康/健康'),
    ready: () => request<ReadyResponse>('/健康/就绪'),
  },
  hermes: {
    chat: (data: HermesChatRequest) =>
      request<HermesChatResponse>('/智能体/hermes/chat', { method: 'POST', body: JSON.stringify(data) }),
  },
};
