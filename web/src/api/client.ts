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
  ProjectListResponse,
  Project,
  ProjectCreateRequest,
  ArtifactListResponse,
  Artifact,
  ConversationResponse,
  ChatResponse,
  StageConfirmResponse,
  StageRejectResponse,
  KanbanBoard,
  KanbanCard,
  CreateCardRequest,
  UpdateCardRequest,
  UpdateCardStatusRequest,
  CardHistoryResponse,
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
    throw new Error('API 密钥无效或未设置');
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
  project: {
    list: () => request<ProjectListResponse>('/项目/'),
    create: (data: ProjectCreateRequest) =>
      request<Project>('/项目/', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => request<Project>(`/项目/${id}`),
    updateStage: (id: string, 阶段: string) =>
      request<Project>(`/项目/${id}/阶段`, { method: 'PUT', body: JSON.stringify({ 阶段 }) }),
    confirm: (id: string, 反馈 = '') =>
      request<StageConfirmResponse>(`/项目/${id}/确认`, { method: 'POST', body: JSON.stringify({ 反馈 }) }),
    reject: (id: string, 反馈 = '') =>
      request<StageRejectResponse>(`/项目/${id}/拒绝`, { method: 'POST', body: JSON.stringify({ 反馈 }) }),
    conversation: {
      get: (projectId: string) => request<ConversationResponse>(`/项目/${projectId}/对话/`),
      sendMessage: (projectId: string, 内容: string) =>
        request<ChatResponse>(`/项目/${projectId}/对话/消息`, { method: 'POST', body: JSON.stringify({ 内容 }) }),
    },
    artifacts: {
      list: (projectId: string) => request<ArtifactListResponse>(`/项目/${projectId}/制品/`),
      get: (projectId: string, artifactId: string) => request<Artifact>(`/项目/${projectId}/制品/${artifactId}`),
    },
  },
  kanban: {
    getProjectBoard: (projectId: string) => request<KanbanBoard>(`/看板/项目/${projectId}`),
    createCard: (data: CreateCardRequest) =>
      request<KanbanCard>('/看板/卡片', { method: 'POST', body: JSON.stringify(data) }),
    getCard: (cardId: string) => request<KanbanCard>(`/看板/卡片/${cardId}`),
    updateCard: (cardId: string, data: UpdateCardRequest) =>
      request<KanbanCard>(`/看板/卡片/${cardId}`, { method: 'PUT', body: JSON.stringify(data) }),
    updateCardStatus: (cardId: string, data: UpdateCardStatusRequest) =>
      request<Record<string, unknown>>(`/看板/卡片/${cardId}/状态`, { method: 'POST', body: JSON.stringify(data) }),
    deleteCard: (cardId: string) =>
      request<Record<string, unknown>>(`/看板/卡片/${cardId}`, { method: 'DELETE' }),
    getCardHistory: (cardId: string) => request<CardHistoryResponse>(`/看板/卡片/${cardId}/历史`),
  },
  autonomousLoop: {
    getStatus: () => request<AutonomousLoopStatus>('/自主循环/状态'),
    start: (data?: { 扫描间隔秒?: number }) =>
      request<Record<string, unknown>>('/自主循环/启动', { method: 'POST', body: JSON.stringify(data ?? {}) }),
    stop: () => request<Record<string, unknown>>('/自主循环/停止', { method: 'POST' }),
    pause: () => request<Record<string, unknown>>('/自主循环/暂停', { method: 'POST' }),
    resume: () => request<Record<string, unknown>>('/自主循环/恢复', { method: 'POST' }),
    getEventLog: (limit = 50) => request<AutonomousLoopEventLog>(`/自主循环/事件日志?限制=${limit}`),
    submitApproval: (cardId: string, 响应: string, 反馈 = '') =>
      request<Record<string, unknown>>(`/自主循环/审批/${cardId}`, { method: 'POST', body: JSON.stringify({ 响应, 反馈 }) }),
  },
};
