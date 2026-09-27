import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("App crashed:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="grid min-h-screen place-items-center bg-[#FBFCFB] p-6">
          <div className="w-full max-w-lg rounded-card border border-line bg-surface p-6">
            <h1 className="text-lg font-bold text-ink">Something went wrong</h1>
            <pre className="mt-3 max-h-48 overflow-auto rounded-lg border border-line bg-canvas p-3 text-xs text-rose">
              {this.state.error.message || String(this.state.error)}
            </pre>
            <p className="mt-3 text-sm text-muted">
              The error above was logged to the console. Reload to continue.
            </p>
            <button
              onClick={() => {
                this.setState({ error: null });
                window.location.reload();
              }}
              className="mt-4 rounded-xl bg-leaf px-4 py-2.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}