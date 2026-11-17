/**
 * @module OnboardingProgress
 * @description Visual step-progress bar for the onboarding wizard.
 */
'use client'

import React from 'react'
import { CheckCircle2 } from 'lucide-react'
import { clsx } from 'clsx'

interface Step {
  number: number
  label: string
  description: string
}

const STEPS: Step[] = [
  { number: 1, label: 'Identity',  description: 'Your business' },
  { number: 2, label: 'Category',  description: 'What you do' },
  { number: 3, label: 'Size',      description: 'Team & revenue' },
  { number: 4, label: 'Locations', description: 'Where you operate' },
  { number: 5, label: 'Confirm',   description: 'Review & submit' },
]

interface Props {
  currentStep: number
  completedSteps: number[]
}

export function OnboardingProgress({ currentStep, completedSteps }: Props) {
  return (
    <div className="w-full">
      {/* Desktop: horizontal stepper */}
      <div className="hidden md:flex items-center justify-between relative">
        {/* connector line behind steps */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-slate-200 z-0" />
        <div
          className="absolute top-5 left-0 h-0.5 bg-brand-primary z-0 transition-all duration-500"
          style={{
            width: `${((Math.max(...completedSteps, 0)) / (STEPS.length - 1)) * 100}%`,
          }}
        />

        {STEPS.map((step) => {
          const isCompleted = completedSteps.includes(step.number)
          const isCurrent   = step.number === currentStep

          return (
            <div key={step.number} className="relative z-10 flex flex-col items-center gap-2">
              <div
                className={clsx(
                  'flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-bold transition-all duration-200',
                  isCompleted
                    ? 'border-brand-primary bg-brand-primary text-white'
                    : isCurrent
                    ? 'border-brand-primary bg-white text-brand-primary shadow-md shadow-blue-100'
                    : 'border-slate-200 bg-white text-slate-400'
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  step.number
                )}
              </div>
              <div className="text-center">
                <p
                  className={clsx(
                    'text-xs font-semibold',
                    isCurrent || isCompleted ? 'text-slate-800' : 'text-slate-400'
                  )}
                >
                  {step.label}
                </p>
                <p className="text-[10px] text-slate-400">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Mobile: simple indicator */}
      <div className="md:hidden flex items-center gap-3 mb-4">
        <div className="flex gap-1.5">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className={clsx(
                'h-1.5 rounded-full transition-all duration-300',
                step.number === currentStep
                  ? 'w-6 bg-brand-primary'
                  : completedSteps.includes(step.number)
                  ? 'w-3 bg-brand-primary opacity-60'
                  : 'w-3 bg-slate-200'
              )}
            />
          ))}
        </div>
        <span className="text-xs text-slate-500 font-medium">
          Step {currentStep} of {STEPS.length} — {STEPS[currentStep - 1]?.label}
        </span>
      </div>
    </div>
  )
}
