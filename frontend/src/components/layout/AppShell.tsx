import type { ReactNode } from 'react';
import { Header } from './Header';
import { BottomNav } from './BottomNav';

interface AppShellProps {
  children: ReactNode;
  watchlistCount?: number;
}

export function AppShell({ children, watchlistCount = 0 }: AppShellProps) {
  return (
    <div className="container">
      <Header />
      <BottomNav watchlistCount={watchlistCount} />
      <main id="main-content">{children}</main>
    </div>
  );
}
