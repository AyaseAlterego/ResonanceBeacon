type Variant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

const variantMap: Record<Variant, string> = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
  info: 'badge-info',
  neutral: 'badge-neutral',
};

const statusToVariant: Record<string, Variant> = {
  healthy: 'success',
  running: 'info',
  completed: 'success',
  pending: 'warning',
  failed: 'danger',
  cancelled: 'neutral',
  已启动: 'info',
  已取消: 'neutral',
  已批准: 'success',
  已拒绝: 'danger',
  ready: 'success',
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const variant = statusToVariant[status] ?? 'neutral';
  return <span className={variantMap[variant]}>{status}</span>;
}

export function getVariant(status: string): Variant {
  return statusToVariant[status] ?? 'neutral';
}
