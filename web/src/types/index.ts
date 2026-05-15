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

export interface PipelineStagesResponse {
  阶段列表: Array<{
    ID: string;
    名称: string;
    阶段类型: string;
    类别: string;
    状态: string;
    顺序: number;
  }>;
}

export interface PipelineArtifactsResponse {
  制品列表: Array<{
    ID: string;
    名称: string;
    制品类型: string;
    文件路径: string;
    大小: number;
  }>;
}

export interface ApprovalHistoryResponse {
  审批历史: Array<{
    ID: string;
    流水线ID: string;
    内容描述: string;
    状态: string;
    决策者: string;
    决策时间: string;
  }>;
}

export type ProjectStage =
  | '需求分析'
  | '架构设计'
  | '方案确认'
  | '开发执行'
  | '代码审查'
  | '完成'
  | '已取消'
  | '失败';

export type ArtifactType = 'spec' | 'plan' | 'code' | 'review';

export type SuperpowersSkill =
  | 'brainstorming'
  | 'writing-plans'
  | 'using-git-worktrees'
  | 'subagent-driven-development'
  | 'test-driven-development'
  | 'requesting-code-review'
  | 'finishing-a-development-branch'
  | 'systematic-debugging'
  | 'verification-before-completion';

export interface Project {
  ID: string;
  名称: string;
  描述: string;
  阶段: ProjectStage;
  工作目录: string;
  创建时间: string;
  更新时间: string;
  制品列表?: Artifact[];
}

export interface ProjectListResponse {
  项目列表: Project[];
  总数: number;
}

export interface ProjectCreateRequest {
  名称: string;
  描述: string;
}

export interface Artifact {
  ID: string;
  项目ID: string;
  制品类型: ArtifactType;
  名称: string;
  内容: string;
  阶段: ProjectStage;
  技能: SuperpowersSkill;
  文件路径: string;
  创建时间: string;
}

export interface ArtifactListResponse {
  制品列表: Artifact[];
  总数: number;
}

export interface ConversationMessage {
  ID: string;
  对话ID: string;
  角色: 'user' | 'hermes' | 'system';
  内容: string;
  元数据: Record<string, unknown>;
  创建时间: string;
}

export interface ConversationResponse {
  对话ID: string;
  项目ID: string;
  消息列表: ConversationMessage[];
}

export interface SkillStatus {
  当前技能: SuperpowersSkill;
  技能阶段: string;
  可推进: boolean;
}

export interface ChatResponse {
  用户消息: ConversationMessage;
  Hermes回复: ConversationMessage;
  项目阶段: ProjectStage;
  阶段产出: Artifact | null;
  技能状态: SkillStatus;
}

export interface StageConfirmResponse {
  项目ID: string;
  原阶段: string;
  新阶段: string;
}

export interface StageRejectResponse {
  项目ID: string;
  阶段: string;
  消息: string;
}
