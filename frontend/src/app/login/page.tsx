'use client'

/**
 * @module LoginPage
 * @description Production-quality login page for ComplianceTracker.
 * Features a two-column layout (decorative brand panel + login form),
 * react-hook-form + zod validation, show/hide password, remember me,
 * and inline API error display.
 */

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  CheckCircle2,
  BarChart3,
  Bell,
  AlertCircle,
} from 'lucide-react'
import Cookies from 'js-cookie'

import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authApi } from '@/lib/api'
import { onboardingApi } from '@/lib/onboardingApi'
import { loginSchema, LoginFormValues } from '@/lib/validations'

// ─── Feature bullets shown on the left decorative panel ──────────────────────

const features = [
  {
    icon: CheckCircle2,
    title: 'Automated Compliance Checks',
    desc: 'Real-time monitoring against regulatory frameworks',
  },
  {
    icon: BarChart3,
    title: 'Audit-Ready Reports',
    desc: 'Generate comprehensive audit trails in one click',
  },
  {
    icon: Bell,
    title: 'Proactive Alerts',
    desc: 'Get notified before compliance deadlines are missed',
  },
]

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Login page with two-column responsive layout and full form validation.
 */
export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    clearErrors,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '', rememberMe: false },
  })

  const onSubmit = async (values: LoginFormValues) => {
    try {
      setApiError(null)
      const tokens = await authApi.login(values.email, values.password)
      const expires = values.rememberMe ? 7 : 1

      Cookies.set('access_token', tokens.access_token, {
        secure: true,
        sameSite: 'strict',
        expires,
      })
      Cookies.set('refresh_token', tokens.refresh_token, {
        secure: true,
        sameSite: 'strict',
        expires: 7,
      })

      // Direct to onboarding if first time, else dashboard
      try {
        const onboardingStatus = await onboardingApi.getStatus()
        if (onboardingStatus.is_onboarded) {
          router.push('/demo')
        } else {
          router.push('/demo')
        }
      } catch {
        router.push('/demo')
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Invalid email or password. Please try again.'

      // Try to extract server error detail
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setApiError(axiosErr?.response?.data?.detail ?? message)
    }
  }

  const handleInputChange = () => {
    if (apiError) setApiError(null)
    clearErrors()
  }

  return (
    <div className="flex min-h-screen">
      {/* ── Left: Decorative Brand Panel (desktop only) ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-brand-primary p-12 text-white">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-9 w-9" aria-hidden="true" />
          <span className="text-2xl font-bold tracking-tight">
            ComplianceTracker
          </span>
        </div>

        {/* Hero text */}
        <div className="space-y-6">
          <h1 className="text-4xl font-extrabold leading-tight">
            Stay compliant.
            <br />
            Stay ahead.
          </h1>
          <p className="text-blue-200 text-lg max-w-sm">
            Your AI-powered partner for navigating complex regulatory landscapes
            with confidence.
          </p>

          {/* Feature bullets */}
          <ul className="space-y-5 mt-8">
            {features.map(({ icon: Icon, title, desc }) => (
              <li key={title} className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <div>
                  <p className="font-semibold">{title}</p>
                  <p className="text-sm text-blue-200">{desc}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer tagline */}
        <p className="text-sm text-blue-300">
          Trusted by compliance teams worldwide.
        </p>
      </div>

      {/* ── Right: Login Form ── */}
      <div className="flex flex-1 items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="w-full max-w-md">
          {/* Mobile logo (shown only on small screens) */}
          <div className="mb-8 flex items-center justify-center gap-2 lg:hidden">
            <ShieldCheck className="h-8 w-8 text-brand-primary" aria-hidden="true" />
            <span className="text-2xl font-bold text-brand-primary">
              ComplianceTracker
            </span>
          </div>

          <div className="rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900">
                Welcome back
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Sign in to your account to continue
              </p>
            </div>

            {/* API Error Banner */}
            {apiError && (
              <div
                role="alert"
                className="mb-5 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3"
              >
                <AlertCircle
                  className="mt-0.5 h-4 w-4 shrink-0 text-red-500"
                  aria-hidden="true"
                />
                <p className="text-sm text-red-700">{apiError}</p>
              </div>
            )}

            <form
              onSubmit={handleSubmit(onSubmit)}
              noValidate
              className="space-y-5"
            >
              {/* Email */}
              <Input
                {...register('email', { onChange: handleInputChange })}
                id="email"
                type="email"
                label="Email address"
                placeholder="you@company.com"
                autoComplete="email"
                error={errors.email?.message}
                leftIcon={<Mail className="h-4 w-4" />}
              />

              {/* Password */}
              <div className="relative">
                <Input
                  {...register('password', { onChange: handleInputChange })}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  label="Password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  error={errors.password?.message}
                  leftIcon={<Lock className="h-4 w-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={
                        showPassword ? 'Hide password' : 'Show password'
                      }
                      className="text-slate-400 hover:text-slate-600 transition-colors"
                      tabIndex={0}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  }
                />
              </div>

              {/* Remember me + Forgot password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    {...register('rememberMe')}
                    type="checkbox"
                    id="rememberMe"
                    className="h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
                  />
                  <span className="text-sm text-slate-600">Remember me</span>
                </label>

                <Link
                  href="/forgot-password"
                  className="text-sm font-medium text-brand-primary hover:text-brand-secondary transition-colors"
                >
                  Forgot your password?
                </Link>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isSubmitting}
                aria-label="Sign in to your account"
              >
                Sign In
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-slate-400 font-medium">
                  or
                </span>
              </div>
            </div>

            {/* Register link */}
            <p className="text-center text-sm text-slate-600">
              Don&apos;t have an account?{' '}
              <Link
                href="/register"
                className="font-semibold text-brand-primary hover:text-brand-secondary transition-colors"
              >
                Create one for free
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
