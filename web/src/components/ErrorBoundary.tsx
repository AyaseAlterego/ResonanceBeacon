import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-dark-950">
          <div className="card max-w-md w-full text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-lg font-semibold text-dark-100">页面出现错误</h2>
            <p className="text-sm text-dark-400">
              {this.state.error?.message || '未知错误'}
            </p>
            <button
              onClick={this.handleRetry}
              className="btn-primary"
            >
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
