import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: string;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="page">
          <div className="error-box">
            <div className="error-icon">💥</div>
            <div className="error-text">Ошибка: {this.state.error}</div>
            <button
              className="btn btn-primary"
              onClick={() => {
                this.setState({ hasError: false, error: '' });
                window.location.reload();
              }}
            >
              Перезагрузить
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
