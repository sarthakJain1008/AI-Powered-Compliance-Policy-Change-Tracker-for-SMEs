'use client'

/**
 * @module RegisterPage
 * @description User registration page with two-column layout, password strength
 * indicator, and full react-hook-form + zod validation.
 */

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'

import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authApi } from '@/lib/api'
import { registerSchema, RegisterFormValues } from '@/lib/validations'

// ─── Password Strength ────────────────────────────────────────────────────────

type StrengthLevel = 'empty' | 'weak' | 'medium' | 'strong'

interface StrengthResult {
  level: StrengthLevel
  score: number
  label: string
  color: string
  barColor: string
}

function getPasswordStrength(password: string): StrengthResult {
  if (!password) {
    return { level: 'empty', score: 0, label: '', color: '', barColor: 'bg-slate-200' }
  }

  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 2) {
    return { level: 'weak', score, label: 'Weak', color: 'text-red-600', barColor: 'bg-red-500' }
  } else if (score <= 4) {
    return { level: 'medium', score, label: 'Medium', color: 'text-yellow-600', barColor: 'bg-yellow-500' }
  } else {
    return { level: 'strong', score, label: 'Strong', color: 'text-green-600', barColor: 'bg-green-500' }
  }
}

// ─── Strength Bar Component ───────────────────────────────────────────────────

function PasswordStrengthBar({ password }: { password: string }) {
  const strength = getPasswordStrength(password)

  if (!password) return null

  const widths = ['w-1/6', 'w-2/6', 'w-3/6', 'w-4/6', 'w-5/6', 'w-full']
  const width = widths[Math.min(strength.score - 1, 5)] ?? 'w-1/6'

  return (
    <div className="mt-2 space-y-1" aria-live="polite">
      <div className="h-1.5 w-full rounded-full bg-slate-200">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${strength.barColor} ${width}`}
        />
      </div>
      <p className={`text-xs font-medium ${strength.color}`}>
        Password strength: {strength.label}
      </p>
    </div>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Registration page with password strength indicator and two-column layout.
 */
export default function RegisterPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
    clearErrors,
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { fullName: '', email: '', password: '', confirmPassword: '' },
  })

  const passwordValue = useWatch({ control, name: 'password' })

  const onSubmit = async (values: RegisterFormValues) => {
    try {
      setApiError(null)
      await authApi.register({
        email: values.email,
        password: values.password,
        full_name: values.fullName || undefined,
      })
      router.push('/login?registered=true')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setApiError(
        axiosErr?.response?.data?.detail ??
          'Registration failed. Please try again.'
      )
    }
  }

  const handleInputChange = () => {
    if (apiError) setApiError(null)
    clearErrors()
  }

  return (
    <div className="flex min-h-screen">
      {/* ── Left: Decorative Brand Panel ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-brand-primary p-12 text-white">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-9 w-9" aria-hidden="true" />
          <span className="text-2xl font-bold tracking-tight">
            ComplianceTracker
          </span>
        </div>

        <div className="space-y-6">
          <h1 className="text-4xl font-extrabold leading-tight">
            Start your compliance
            <br />
            journey today.
          </h1>
          <p className="text-blue-200 text-lg max-w-sm">
            Join thousands of teams using AI to simplify regulatory compliance
            and audit management.
          </p>

          <ul className="mt-8 space-y-4">
            {[
              'Free 14-day trial, no credit card required',
              'Set up in under 5 minutes',
              'SOC 2 Type II certified infrastructure',
            ].map((item) => (
              <li key={item} className="flex items-center gap-3 text-blue-100">
                <CheckCircle2
                  className="h-5 w-5 shrink-0 text-blue-300"
                  aria-hidden="true"
                />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-sm text-blue-300">
          Already have an account?{' '}
          <Link
            href="/login"
            className="font-semibold text-white underline hover:no-underline"
          >
            Sign in
          </Link>
        </p>
      </div>

      {/* ── Right: Register Form ── */}
      <div className="flex flex-1 items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center justify-center gap-2 lg:hidden">
            <ShieldCheck className="h-8 w-8 text-brand-primary" aria-hidden="true" />
            <span className="text-2xl font-bold text-brand-primary">
              ComplianceTracker
            </span>
          </div>

          <div className="rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900">
                Create your account
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Fill in the details below to get started
              </p>
            </div>

            {/* API Error */}
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
              {/* Full Name */}
              <Input
                {...register('fullName', { onChange: handleInputChange })}
                id="fullName"
                type="text"
                label="Full name (optional)"
                placeholder="Jane Smith"
                autoComplete="name"
                error={errors.fullName?.message}
                leftIcon={<User className="h-4 w-4" />}
              />

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
              <div>
                <Input
                  {...register('password', { onChange: handleInputChange })}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  label="Password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  error={errors.password?.message}
                  leftIcon={<Lock className="h-4 w-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      className="text-slate-400 hover:text-slate-600 transition-colors"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  }
                />
                <PasswordStrengthBar password={passwordValue ?? ''} />
              </div>

              {/* Confirm Password */}
              <Input
                {...register('confirmPassword', { onChange: handleInputChange })}
                id="confirmPassword"
                type={showConfirm ? 'text' : 'password'}
                label="Confirm password"
                placeholder="••••••••"
                autoComplete="new-password"
                error={errors.confirmPassword?.message}
                leftIcon={<Lock className="h-4 w-4" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowConfirm((v) => !v)}
                    aria-label={showConfirm ? 'Hide password' : 'Show password'}
                    className="text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showConfirm ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                }
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isSubmitting}
                aria-label="Create account"
              >
                Create Account
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-slate-400 font-medium">or</span>
              </div>
            </div>

            <p className="text-center text-sm text-slate-600">
              Already have an account?{' '}
              <Link
                href="/login"
                className="font-semibold text-brand-primary hover:text-brand-secondary transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
