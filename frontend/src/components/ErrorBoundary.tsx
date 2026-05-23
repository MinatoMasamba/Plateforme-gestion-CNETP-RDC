import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-screen bg-[#020204] flex flex-col items-center justify-center gap-6 p-6">
          <AlertTriangle className="h-12 w-12 text-red-500" />
          <div className="text-center max-w-md">
            <h1 className="text-xl font-bold text-slate-200 mb-2">Erreur d'Application</h1>
            <p className="text-sm text-slate-400 mb-4">
              Une erreur est survenue lors du chargement de l'application.
            </p>
            {this.state.error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 text-left">
                <p className="text-xs font-mono text-red-300 break-words">
                  {this.state.error.message}
                </p>
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition"
            >
              <RefreshCw className="h-4 w-4" />
              Réessayer
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
