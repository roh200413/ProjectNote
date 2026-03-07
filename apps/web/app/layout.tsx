import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ProjectNote Web',
  description: 'Monorepo web app bootstrap',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
