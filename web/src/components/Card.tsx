import { type ReactNode } from 'react';

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

export default function Card({ title, children, className = '', action }: CardProps) {
  return (
    <div className={`card ${className}`}>
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-dark-200">{title}</h3>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
