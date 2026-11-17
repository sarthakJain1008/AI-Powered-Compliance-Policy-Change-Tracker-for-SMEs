'use client'

/**
 * @module OnboardingPage
 * @description Multi-step onboarding wizard shell.
 * Checks auth on mount, redirects already-onboarded users to /dashboard.
 */

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ShieldCheck } from 'lucide-react'

import { OnboardingProvider, useOnboarding } from '@/components/onboarding/OnboardingContext'
import { OnboardingProgress } from '@/components/onboarding/OnboardingProgress'
import { StepIdentity }   from '@/components/onboarding/StepIdentity'
import { StepSector }     from '@/components/onboarding/StepSector'
import { StepSize }       from '@/components/onboarding/StepSize'
import { StepLocations }  from '@/components/onboarding/StepLocations'
import { StepReview }     from '@/components/onboarding/StepReview'
import { onboardingApi }  from '@/lib/onboardingApi'
import { authApi }        from '@/lib/api'

function WizardContent() {
  const router = useRouter()
  const { currentStep, setStep, isStepComplete } = useOnboarding()

  const completedSteps = [1, 2, 3, 4].filter((s) => s < currentStep && isStepComplete(s))

  const goNext = () => setStep((prev: number) => Math.min(prev + 1, 5))
  const goBack = () => setStep((prev: number) => Math.max(prev - 1, 1))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto max-w-3xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-primary text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="text-sm font-bold text-slate-900">ComplianceTracker</span>
          </div>
          <span className="text-xs text-slate-400">Setting up your compliance profile</span>
        </div>
      </header>

      {/* Body */}
      <main className="mx-auto max-w-3xl px-6 py-8">
        {/* Progress Bar */}
        <div className="mb-10">
          <OnboardingProgress currentStep={currentStep} completedSteps={completedSteps} />
        </div>

        {/* Step Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          {currentStep === 1 && <StepIdentity onNext={goNext} />}
          {currentStep === 2 && <StepSector   onNext={goNext} onBack={goBack} />}
          {currentStep === 3 && <StepSize     onNext={goNext} onBack={goBack} />}
          {currentStep === 4 && <StepLocations onNext={goNext} onBack={goBack} />}
          {currentStep === 5 && (
            <StepReview
              onBack={goBack}
              onEditStep={(step) => setStep(step)}
            />
          )}
        </div>

        {/* Footer note */}
        <p className="mt-6 text-center text-xs text-slate-400">
          Your data is used only to personalise your compliance calendar. It is never shared with third parties.
        </p>
      </main>
    </div>
  )
}

export default function OnboardingPage() {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    // Guard: must be authenticated
    authApi.getMe()
      .then(async () => {
        // If already onboarded, skip to dashboard
        const status = await onboardingApi.getStatus()
        if (status.is_onboarded) {
          router.replace('/dashboard')
        } else {
          setChecking(false)
        }
      })
      .catch(() => {
        router.replace('/login')
      })
  }, [router])

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center gap-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-primary" />
        <p className="text-sm text-slate-500 font-medium">Checking your session…</p>
      </div>
    )
  }

  return (
    <OnboardingProvider>
      <WizardContent />
    </OnboardingProvider>
  )
}
