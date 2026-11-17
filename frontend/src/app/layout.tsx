/**
 * @module RootLayout
 * @description Root Next.js 14 App Router layout. Applies the Inter font,
 * global styles, and sets page-level metadata for the entire application.
 */

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'ComplianceTracker',
    template: '%s | ComplianceTracker',
  },
  description:
    'AI-Powered Compliance Tracker — Stay compliant. Stay ahead.',
  keywords: ['compliance', 'tracker', 'AI', 'regulatory', 'audit'],
}

interface RootLayoutProps {
  children: React.ReactNode
}

/**
 * Root layout wrapping all pages with font and global CSS.
 */
export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
