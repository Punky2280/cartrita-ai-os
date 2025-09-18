/**
 * Next.js Not Found Page - Cartrita AI OS v2
 *
 * Custom 404 error page with proper metadata
 */

import { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: '404 - Page Not Found | Cartrita AI OS v2',
  description: 'The page you are looking for could not be found.',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#6e81ff',
};

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 text-gray-100">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-copilot-blue">404</h1>
        <h2 className="text-2xl font-semibold">Page Not Found</h2>
        <p className="text-gray-400 max-w-md">
          The page you are looking for might have been removed, had its name changed,
          or is temporarily unavailable.
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-3 bg-copilot-blue hover:bg-primary-600
                     text-white rounded-lg transition-colors font-medium"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
