'use client'

/**
 * @module AuthCard
 * @description Card wrapper component for all authentication pages.
 * Renders the app logo, title, optional subtitle, and a children slot for form content.
 */

import React from 'react'
import { ShieldCheck } from 'lucide-react'

interface AuthCardProps {
  /** Subtitle displayed below the app logo */
  subtitle?: string
  /** Form content and other child elements */
  children: React.ReactNode
}

/**
 * Centered card container used on login, register, and password pages.
 * Displays the ComplianceTracker brand at the top.
 */
export function AuthCard({ subtitle, children }: AuthCardProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--auth-bg)] p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 p-8">
        {/* Logo + Brand */}
        <div className="mb-6 flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck
              className="h-8 w-8 text-brand-primary"
              aria-hidden="true"
            />
            <span className="text-2xl font-bold tracking-tight text-brand-primary">
              ComplianceTracker
            </span>
          </div>

          {subtitle && (
            <p className="text-center text-sm text-slate-500">{subtitle}</p>
          )}
        </div>

        {/* Form Content */}
        <div>{children}</div>
      </div>
    </div>
  )
}
