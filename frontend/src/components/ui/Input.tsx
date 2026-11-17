'use client'

/**
 * @module Input
 * @description Reusable, accessible form input component with label, error,
 * helper text, and optional left/right icon slots.
 */

import React from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Label displayed above the input */
  label?: string
  /** Error message shown below the input (triggers red styling) */
  error?: string
  /** Helper text shown below the input (hidden when error is set) */
  helperText?: string
  /** Icon component rendered on the left inside the input */
  leftIcon?: React.ReactNode
  /** Icon component rendered on the right inside the input */
  rightIcon?: React.ReactNode
}

function cn(...inputs: Parameters<typeof clsx>): string {
  return twMerge(clsx(...inputs))
}

/**
 * Fully accessible input component with optional label, icons, and error state.
 * Uses React.forwardRef for compatibility with react-hook-form.
 */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      id,
      className,
      ...props
    },
    ref
  ) => {
    const inputId = id ?? `input-${Math.random().toString(36).slice(2, 9)}`
    const errorId = `${inputId}-error`
    const helperId = `${inputId}-helper`
    const hasError = Boolean(error)

    return (
      <div className="flex flex-col gap-1 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-slate-700"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <span
              className="pointer-events-none absolute left-3 flex items-center text-slate-400"
              aria-hidden="true"
            >
              {leftIcon}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? errorId : helperText ? helperId : undefined
            }
            className={cn(
              'w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-900',
              'placeholder:text-slate-400',
              'shadow-sm',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-1',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              hasError
                ? 'border-red-500 focus:border-red-500 focus:ring-red-300'
                : 'border-surface-border focus:border-brand-primary focus:ring-blue-200',
              'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500',
              className
            )}
            {...props}
          />

          {rightIcon && (
            <span className="absolute right-3 flex items-center">
              {rightIcon}
            </span>
          )}
        </div>

        {hasError && (
          <p
            id={errorId}
            role="alert"
            className="text-xs text-red-600 mt-0.5"
          >
            {error}
          </p>
        )}

        {!hasError && helperText && (
          <p
            id={helperId}
            className="text-xs text-slate-500 mt-0.5"
          >
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
