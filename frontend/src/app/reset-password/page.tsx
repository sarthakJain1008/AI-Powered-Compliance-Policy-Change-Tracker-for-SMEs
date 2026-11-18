'use client'

/**
 * @module ResetPasswordPage
 * @description Reset Password page for ComplianceTracker.
 * Reads the reset token from the URL search params (?token=xyz), validates it,
 * and allows the user to set a new password with confirmation and strength checks.
 */

import React, { useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  KeyRound,
} from 'lucide-react'

import { authApi } from '@/lib/api'
import { resetPasswordSchema, type ResetPasswordFormValues } from '@/lib/validations'
import { AuthCard } from '@/components/ui/AuthCard'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      token: token,
      newPassword: '',
      confirmPassword: '',
    },
  })

  const newPassword = watch('newPassword', '')

  // Simple password strength calculation
  const getPasswordStrength = (pwd: string) => {
    let score = 0
    if (pwd.length >= 8) score++
    if (/[A-Z]/.test(pwd)) score++
    if (/[a-z]/.test(pwd)) score++
    if (/[0-9]/.test(pwd)) score++
    if (/[^A-Za-z0-9]/.test(pwd)) score++
    return score
  }

  const strength = getPasswordStrength(newPassword)

  const onSubmit = async (values: ResetPasswordFormValues) => {
    setServerError(null)
    try {
      await authApi.resetPassword(token, values.newPassword)
      setIsSuccess(true)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setServerError(
          axiosErr.response?.data?.detail ??
            'Failed to reset password. The link may have expired or is invalid.'
        )
      } else {
        setServerError('An unexpected error occurred. Please try again.')
      }
    }
  }

  // Token missing in query params
  if (!token) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <AuthCard
          title="Invalid Reset Link"
          subtitle="This password reset link is invalid or incomplete."
        >
          <div className="space-y-6 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
              <AlertCircle className="h-7 w-7" />
            </div>
            <p className="text-sm text-slate-600">
              Please request a new password reset link from the forgot password page.
            </p>
            <Link
              href="/forgot-password"
              className="inline-flex w-full justify-center rounded-lg bg-brand-primary px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2"
            >
              Request New Link
            </Link>
          </div>
        </AuthCard>
      </div>
    )
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <AuthCard
          title="Password Updated"
          subtitle="Your password has been successfully reset."
        >
          <div className="space-y-6 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <p className="text-sm text-slate-600">
              You can now sign in to your ComplianceTracker account using your new password.
            </p>
            <Button
              type="button"
              fullWidth
              onClick={() => router.push('/login')}
            >
              Back to Sign In
            </Button>
          </div>
        </AuthCard>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <AuthCard
        title="Set New Password"
        subtitle="Please enter and confirm your new secure password."
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {serverError && (
            <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500 mt-0.5" />
              <div>
                <p className="font-medium">Reset Failed</p>
                <p className="mt-0.5">{serverError}</p>
              </div>
            </div>
          )}

          {/* Hidden token field */}
          <input type="hidden" {...register('token')} value={token} />

          {/* New Password */}
          <div>
            <Input
              id="newPassword"
              type={showPassword ? 'text' : 'password'}
              label="New Password"
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-slate-400 hover:text-slate-600 focus:outline-none"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              }
              error={errors.newPassword?.message}
              {...register('newPassword')}
            />

            {/* Strength Meter */}
            {newPassword.length > 0 && (
              <div className="mt-2 space-y-1.5">
                <div className="flex h-1.5 w-full gap-1 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full transition-all duration-300 ${
                      strength <= 2
                        ? 'w-1/3 bg-red-500'
                        : strength <= 4
                        ? 'w-2/3 bg-amber-500'
                        : 'w-full bg-emerald-500'
                    }`}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Strength</span>
                  <span className="font-medium">
                    {strength <= 2
                      ? 'Weak'
                      : strength <= 4
                      ? 'Moderate'
                      : 'Strong'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <Input
            id="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            label="Confirm New Password"
            placeholder="••••••••"
            leftIcon={<KeyRound className="h-4 w-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            }
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          <Button type="submit" fullWidth isLoading={isSubmitting}>
            Reset Password
          </Button>

          <div className="text-center pt-2">
            <Link
              href="/login"
              className="inline-flex items-center text-sm font-medium text-slate-600 hover:text-slate-900"
            >
              <ArrowLeft className="mr-1.5 h-4 w-4" /> Back to Sign In
            </Link>
          </div>
        </form>
      </AuthCard>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary" />
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  )
}
