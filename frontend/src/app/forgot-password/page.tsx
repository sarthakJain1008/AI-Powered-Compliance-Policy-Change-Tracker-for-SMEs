'use client'

/**
 * @module ForgotPasswordPage
 * @description Password reset request page. Shows email form initially;
 * on success switches to a "check your email" state with a 60-second
 * resend countdown timer.
 */

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  Mail,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react'

import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authApi } from '@/lib/api'
import { forgotPasswordSchema, ForgotPasswordFormValues } from '@/lib/validations'

const RESEND_COOLDOWN = 60

/**
 * Forgot password page with two states: form and email-sent confirmation.
 */
export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)
  const [resendCooldown, setResendCooldown] = useState(0)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    clearErrors,
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  })

  // Countdown timer for resend button
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendCooldown])

  const onSubmit = async (values: ForgotPasswordFormValues) => {
    try {
      setApiError(null)
      await authApi.forgotPassword(values.email)
      setSubmittedEmail(values.email)
      setSubmitted(true)
      setResendCooldown(RESEND_COOLDOWN)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setApiError(
        axiosErr?.response?.data?.detail ??
          'Something went wrong. Please try again.'
      )
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    try {
      setApiError(null)
      await authApi.forgotPassword(submittedEmail)
      setResendCooldown(RESEND_COOLDOWN)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setApiError(axiosErr?.response?.data?.detail ?? 'Failed to resend. Try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <ShieldCheck className="h-8 w-8 text-brand-primary" aria-hidden="true" />
          <span className="text-2xl font-bold text-brand-primary">
            ComplianceTracker
          </span>
        </div>

        <div className="rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 p-8">
          {/* Back link */}
          <Link
            href="/login"
            className="mb-6 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            aria-label="Back to sign in"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to sign in
          </Link>

          {/* ── SUCCESS STATE ── */}
          {submitted ? (
            <div className="text-center space-y-5">
              <div className="flex justify-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle2
                    className="h-8 w-8 text-green-600"
                    aria-hidden="true"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <h2 className="text-xl font-bold text-slate-900">
                  Check your email
                </h2>
                <p className="text-sm text-slate-500">
                  We sent a password reset link to{' '}
                  <span className="font-medium text-slate-700">
                    {submittedEmail}
                  </span>
                </p>
                <p className="text-xs text-slate-400">
                  Didn&apos;t receive it? Check your spam folder or resend below.
                </p>
              </div>

              {apiError && (
                <div
                  role="alert"
                  className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-left"
                >
                  <AlertCircle
                    className="mt-0.5 h-4 w-4 shrink-0 text-red-500"
                    aria-hidden="true"
                  />
                  <p className="text-sm text-red-700">{apiError}</p>
                </div>
              )}

              <Button
                type="button"
                variant="secondary"
                size="md"
                fullWidth
                onClick={handleResend}
                disabled={resendCooldown > 0}
                aria-label={
                  resendCooldown > 0
                    ? `Resend email in ${resendCooldown}s`
                    : 'Resend email'
                }
              >
                {resendCooldown > 0
                  ? `Resend email (${resendCooldown}s)`
                  : 'Resend email'}
              </Button>
            </div>
          ) : (
            /* ── FORM STATE ── */
            <>
              <div className="mb-6 space-y-1">
                <h2 className="text-2xl font-bold text-slate-900">
                  Reset your password
                </h2>
                <p className="text-sm text-slate-500">
                  Enter your email and we&apos;ll send you a reset link
                </p>
              </div>

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
                <Input
                  {...register('email', {
                    onChange: () => {
                      if (apiError) setApiError(null)
                      clearErrors()
                    },
                  })}
                  id="email"
                  type="email"
                  label="Email address"
                  placeholder="you@company.com"
                  autoComplete="email"
                  error={errors.email?.message}
                  leftIcon={<Mail className="h-4 w-4" />}
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  isLoading={isSubmitting}
                  aria-label="Send reset link"
                >
                  Send Reset Link
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
