import type { ReactNode } from 'react';
import { Header } from './Header';
import { BottomNav } from './BottomNav';
import { useUIStore } from '../../stores/uiStore';
import { X } from 'lucide-react';

interface AppShellProps {
  children: ReactNode;
  watchlistCount?: number;
}

export function AppShell({ children, watchlistCount = 0 }: AppShellProps) {
  const { notification, dismissNotification } = useUIStore();

  return (
    <div className="container">
      <Header />

      {/* Notification Banner */}
      {notification && (
        <div
          style={{
            position: 'fixed',
            top: '60px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '90%',
            maxWidth: '400px',
            padding: '12px 16px',
            backgroundColor: notification.type === 'success' ? 'var(--primary)' :
              notification.type === 'error' ? '#ef4444' : 'var(--bg-secondary)',
            color: notification.type === 'info' ? 'var(--text-primary)' : '#fff',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            animation: 'slideDown 0.3s ease'
          }}
        >
          <span style={{ flex: 1, fontSize: '14px', fontWeight: '500' }}>
            {notification.message}
          </span>
          {notification.action && (
            <button
              onClick={() => {
                notification.action?.onClick();
                dismissNotification();
              }}
              style={{
                padding: '6px 12px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'inherit',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {notification.action.label}
            </button>
          )}
          <button
            onClick={dismissNotification}
            style={{
              background: 'none',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              padding: '4px',
              opacity: 0.8
            }}
          >
            <X size={18} />
          </button>
        </div>
      )}

      <BottomNav watchlistCount={watchlistCount} />
      <main id="main-content">{children}</main>

      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
