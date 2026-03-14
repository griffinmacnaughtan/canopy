import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Custom fallback UI. If omitted, a default card is shown. */
  fallback?: ReactNode;
  /** Display name shown in the error card heading. */
  name?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary — catches render-time exceptions in its subtree and
 * renders a recovery UI instead of crashing the whole page.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary name="Portfolio Chart">
 *   <MyChart />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production you'd send this to an error tracking service (Sentry, etc.)
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="rounded-xl border border-red-200 bg-red-50/60 p-6 text-center">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-red-400" />
          <h3 className="mb-1 text-sm font-semibold text-red-700">
            {this.props.name ? `${this.props.name} failed to render` : "Something went wrong"}
          </h3>
          <p className="mb-4 text-xs text-red-500/80">
            {this.state.error?.message ?? "An unexpected error occurred in this component."}
          </p>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-1.5 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-200 transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
