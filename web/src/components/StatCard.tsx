interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

export default function StatCard({ label, value, sub, color = 'text-accent-400' }: StatCardProps) {
  return (
    <div className="card">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color} font-mono`}>{value}</p>
      {sub && <p className="text-xs text-dark-500 mt-1">{sub}</p>}
    </div>
  );
}
