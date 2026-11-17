'use client'

/**
 * @module DashboardPage
 * @description Secure authenticated dashboard landing page for ComplianceTracker.
 * Checks JWT authentication status, displays user profile information and role,
 * and allows logging out.
 */

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  ShieldCheck,
  LogOut,
  User,
  Building2,
  CalendarCheck2,
  AlertTriangle,
  FileText,
  Clock,
  Sparkles,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated, logout } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-primary" />
        <p className="mt-4 text-sm text-slate-500 font-medium">Loading session...</p>
      </div>
    )
  }

  const handleLogout = () => {
    logout()
    router.replace('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary text-white shadow-sm">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 tracking-tight leading-none">
              ComplianceTracker
            </h1>
            <span className="text-xs text-slate-500 font-normal">
              AI-Powered SME Regulatory Engine
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700">
            <User className="h-3.5 w-3.5 text-slate-500" />
            <span>{user.email}</span>
            <span className="ml-1 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-brand-primary uppercase">
              {user.role}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-slate-600 hover:text-red-600"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </Button>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Welcome Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-brand-primary to-blue-700 p-8 text-white shadow-md">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-blue-100 text-xs font-semibold uppercase tracking-wider">
                <Sparkles className="h-4 w-4" /> Authenticated Session Active
              </div>
              <h2 className="mt-1 text-2xl font-bold tracking-tight">
                Welcome back, {user.full_name || user.email.split('@')[0]}!
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-blue-100">
                Your company regulatory shield is active. All versioned acts and circulars are being monitored.
              </p>
            </div>
            <div className="mt-4 md:mt-0 flex gap-3">
              <span className="inline-flex items-center gap-1.5 rounded-xl bg-white/10 backdrop-blur px-3.5 py-2 text-xs font-medium text-white border border-white/20">
                <Building2 className="h-4 w-4" /> Single SME Tenant
              </span>
            </div>
          </div>
        </div>

        {/* Status Cards Grid */}
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
              <span>ACTIVE OBLIGATIONS</span>
              <CalendarCheck2 className="h-4 w-4 text-brand-primary" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">45</span>
              <span className="text-xs text-emerald-600 font-medium">Seeded</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">Statutory calendar obligations</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
              <span>STATUTES MONITORED</span>
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">35</span>
              <span className="text-xs text-slate-500">Central & State</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">Companies Act, GST, DPDP, Labour</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
              <span>SECTOR MAPPINGS</span>
              <Building2 className="h-4 w-4 text-purple-600" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">262</span>
              <span className="text-xs text-purple-600 font-medium">NIC Aligned</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">16 Industry sectors covered</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
              <span>COMPLIANCE HEALTH</span>
              <AlertTriangle className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-600">Secure</span>
              <span className="text-xs text-emerald-600 font-medium">0 Overdue</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">All filings current</p>
          </div>
        </div>

        {/* Phase Notification */}
        <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-600">
            <Clock className="h-6 w-6" />
          </div>
          <h3 className="mt-3 text-base font-semibold text-slate-900">
            Authentication Phase Complete
          </h3>
          <p className="mt-1.5 text-sm text-slate-500 max-w-md mx-auto">
            You are securely authenticated using JWT with bcrypt password hashing.
            The Next.js 14 frontend and FastAPI backend are fully connected.
          </p>
        </div>
      </main>
    </div>
  )
}
