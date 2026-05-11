import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-6 h-6 text-accent-500 animate-spin" />
    </div>
  );
}
