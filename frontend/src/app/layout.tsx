/**
 * Next.js App Layout - Cartrita AI OS v2
 *
 * Root layout with providers and metadata
 */

import { Inter } from 'next/font/google';
import { Metadata } from 'next';
import { Provider } from 'jotai';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import '../styles/globals-v2.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Cartrita AI OS v2',
  description: 'Next-generation AI orchestration platform with multi-agent collaboration',
  keywords: ['AI', 'agents', 'orchestration', 'chat', 'automation'],
  authors: [{ name: 'Cartrita AI Team' }],
  openGraph: {
    title: 'Cartrita AI OS v2',
    description: 'Next-generation AI orchestration platform',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Cartrita AI OS v2',
    description: 'Next-generation AI orchestration platform',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#6e81ff',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="bg-gray-950 text-gray-100 antialiased">
        <Provider>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </Provider>
      </body>
    </html>
  );
}
