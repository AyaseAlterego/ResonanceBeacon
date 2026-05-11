export interface Pipeline {
  ID: string;
  名称: string;
  状态: string;
  阶段数: number;
  完成阶段数: number;
}

export interface PipelineListResponse {
  流水线列表: Pipeline[];
  总数: number;
}

export interface PipelineCreateRequest {
  名称: string;
  描述: string;
  流水线定义: Record<string, unknown>;
  类别?: string | null;
}

export interface PipelineRunRequest {
  流水线ID: string;
  用户输入?: string;
}

export interface Agent {
  ID: string;
  名称: string;
  类别: string;
  状态: string;
  负载: number;
}

export interface AgentListResponse {
  智能体列表: Agent[];
  总数: number;
}

export interface AgentHealthResponse {
  智能体ID: string;
  健康: boolean;
  消息: string;
}

export interface AgentLoadResponse {
  智能体ID: string;
  当前并发: number;
  最大并发: number;
  负载率: number;
}

export interface Approval {
  ID: string;
  流水线ID: string;
  阶段ID: string;
  状态: string;
  风险级别: string;
  创建时间: string;
}

export interface ApprovalDecisionRequest {
  决策者: string;
  批准: boolean;
  反馈?: string;
}

export interface PendingApprovalsResponse {
  待处理审批列表: Approval[];
  总数: number;
}

export interface ConfigResponse {
  配置: Record<string, unknown>;
  来源: string;
}

export interface HealthResponse {
  状态: string;
  服务: string;
  版本: string;
  时间: string;
}

export interface ReadyResponse {
  状态: string;
  数据库: string;
  智能体: string;
}

export interface HermesChatRequest {
  message: string;
}

export interface HermesChatResponse {
  reply: string;
}
