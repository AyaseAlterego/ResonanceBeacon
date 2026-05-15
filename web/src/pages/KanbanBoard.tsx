import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { KanbanBoard, KanbanCard } from '../types';

const 优先级颜色: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-green-500',
};

const 状态标签: Record<string, string> = {
  backlog: '待办',
  in_progress: '进行中',
  review: '审查中',
  done: '已完成',
  cancelled: '已取消',
};

export default function KanbanBoardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [看板, set看板] = useState<KanbanBoard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [新卡片, set新卡片] = useState({ 标题: '', 描述: '', 优先级: 'medium' });

  useEffect(() => {
    if (projectId) {
      加载看板();
    }
  }, [projectId]);

  const 加载看板 = async () => {
    try {
      setLoading(true);
      const 数据 = await api.kanban.getProjectBoard(projectId!);
      set看板(数据);
    } catch (err) {
      setError('加载看板失败');
    } finally {
      setLoading(false);
    }
  };

  const 创建卡片 = async () => {
    try {
      await api.kanban.createCard({
        项目ID: projectId!,
        标题: 新卡片.标题,
        描述: 新卡片.描述,
        优先级: 新卡片.优先级,
      });
      setShowCreateModal(false);
      set新卡片({ 标题: '', 描述: '', 优先级: 'medium' });
      加载看板();
    } catch (err) {
      setError('创建卡片失败');
    }
  };

  const 转换状态 = async (卡片ID: string, 目标状态: string) => {
    try {
      await api.kanban.updateCardStatus(卡片ID, { 目标状态, 原因: '手动拖拽' });
      加载看板();
    } catch (err) {
      setError('状态转换失败');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  if (!看板) {
    return <div className="text-gray-500 p-4">暂无看板数据</div>;
  }

  const 列定义 = [
    { key: 'backlog', 标题: 'Backlog', 颜色: 'border-gray-400' },
    { key: 'in_progress', 标题: 'In Progress', 颜色: 'border-blue-400' },
    { key: 'review', 标题: 'Review', 颜色: 'border-purple-400' },
    { key: 'done', 标题: 'Done', 颜色: 'border-green-400' },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="text-gray-500 hover:text-gray-700"
          >
            ← 返回项目
          </button>
          <h1 className="text-xl font-semibold">Kanban 看板</h1>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          + 新建卡片
        </button>
      </div>

      {/* 看板列 */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-4 min-w-max">
          {列定义.map(列 => (
            <div
              key={列.key}
              className={`w-72 flex-shrink-0 border-t-4 ${列.颜色} bg-gray-50 rounded-lg`}
            >
              <div className="p-3 font-medium text-gray-700 border-b">
                {列.标题}
                <span className="ml-2 text-sm text-gray-500">
                  {看板[列.key as keyof KanbanBoard]?.length || 0}
                </span>
              </div>
              <div className="p-2 space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
                {(看板[列.key as keyof KanbanBoard] as KanbanCard[] || []).map(卡片 => (
                  <div
                    key={卡片.ID}
                    className="bg-white p-3 rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => navigate(`/projects/${projectId}/cards/${卡片.ID}`)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-medium text-sm">{卡片.标题}</h3>
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${优先级颜色[卡片.优先级] || 'bg-gray-400'}`}
                      />
                    </div>
                    {卡片.描述 && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{卡片.描述}</p>
                    )}
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                      <span>{卡片.负责人}</span>
                      {卡片.等待审批 && (
                        <span className="text-orange-500">等待审批</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 创建卡片弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-lg font-semibold mb-4">新建卡片</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">标题</label>
                <input
                  type="text"
                  value={新卡片.标题}
                  onChange={e => set新卡片({ ...新卡片, 标题: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="输入卡片标题"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">描述</label>
                <textarea
                  value={新卡片.描述}
                  onChange={e => set新卡片({ ...新卡片, 描述: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="输入卡片描述"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">优先级</label>
                <select
                  value={新卡片.优先级}
                  onChange={e => set新卡片({ ...新卡片, 优先级: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="critical">紧急</option>
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={创建卡片}
                disabled={!新卡片.标题}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
