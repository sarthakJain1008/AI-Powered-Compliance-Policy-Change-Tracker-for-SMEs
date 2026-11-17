/**
 * @module OnboardingContext
 * @description Global state context for the multi-step onboarding wizard.
 * Holds in-memory step data, options fetched from the API, and navigation helpers.
 */
'use client'

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { onboardingApi, type OnboardingOptions } from '@/lib/onboardingApi'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Step1Data {
  company_name: string
  entity_type: string
  year_of_incorporation: number | null
  cin_llpin: string
  is_dpiit_startup: boolean
}

export interface Step2Data {
  primary_sector_id: number | null
  primary_sector_name: string
  business_sub_type: string
  is_startup: boolean
  startup_stage: string
}

export interface Step3Data {
  employee_range: string
  turnover_range: string
  funding_stage: string
}

export interface Step4Data {
  primary_state: string
  primary_jurisdiction_id: number | null
  operating_states: string[]
  exports_business: boolean
  export_markets: string[]
}

export interface OnboardingState {
  step1: Step1Data
  step2: Step2Data
  step3: Step3Data
  step4: Step4Data
}

interface OnboardingContextValue {
  currentStep: number
  state: OnboardingState
  options: OnboardingOptions | null
  isLoadingOptions: boolean
  setStep: (step: number) => void
  updateStep1: (data: Partial<Step1Data>) => void
  updateStep2: (data: Partial<Step2Data>) => void
  updateStep3: (data: Partial<Step3Data>) => void
  updateStep4: (data: Partial<Step4Data>) => void
  isStepComplete: (step: number) => boolean
}

// ─── Defaults ────────────────────────────────────────────────────────────────

const DEFAULT_STATE: OnboardingState = {
  step1: {
    company_name: '',
    entity_type: '',
    year_of_incorporation: null,
    cin_llpin: '',
    is_dpiit_startup: false,
  },
  step2: {
    primary_sector_id: null,
    primary_sector_name: '',
    business_sub_type: '',
    is_startup: false,
    startup_stage: '',
  },
  step3: {
    employee_range: '',
    turnover_range: '',
    funding_stage: '',
  },
  step4: {
    primary_state: '',
    primary_jurisdiction_id: null,
    operating_states: [],
    exports_business: false,
    export_markets: [],
  },
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null)

// ─── Provider ─────────────────────────────────────────────────────────────────

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [state, setState] = useState<OnboardingState>(DEFAULT_STATE)
  const [options, setOptions] = useState<OnboardingOptions | null>(null)
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)

  useEffect(() => {
    onboardingApi.getOptions()
      .then(setOptions)
      .catch(console.error)
      .finally(() => setIsLoadingOptions(false))
  }, [])

  const updateStep1 = useCallback((data: Partial<Step1Data>) => {
    setState(prev => ({ ...prev, step1: { ...prev.step1, ...data } }))
  }, [])

  const updateStep2 = useCallback((data: Partial<Step2Data>) => {
    setState(prev => ({ ...prev, step2: { ...prev.step2, ...data } }))
  }, [])

  const updateStep3 = useCallback((data: Partial<Step3Data>) => {
    setState(prev => ({ ...prev, step3: { ...prev.step3, ...data } }))
  }, [])

  const updateStep4 = useCallback((data: Partial<Step4Data>) => {
    setState(prev => ({ ...prev, step4: { ...prev.step4, ...data } }))
  }, [])

  const isStepComplete = useCallback(
    (step: number): boolean => {
      switch (step) {
        case 1:
          return !!(state.step1.company_name && state.step1.entity_type)
        case 2:
          return !!(state.step2.primary_sector_id && state.step2.primary_sector_name)
        case 3:
          return !!(state.step3.employee_range && state.step3.turnover_range)
        case 4:
          return !!state.step4.primary_state
        default:
          return false
      }
    },
    [state]
  )

  return (
    <OnboardingContext.Provider
      value={{
        currentStep,
        state,
        options,
        isLoadingOptions,
        setStep: setCurrentStep,
        updateStep1,
        updateStep2,
        updateStep3,
        updateStep4,
        isStepComplete,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  )
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext)
  if (!ctx) throw new Error('useOnboarding must be used within OnboardingProvider')
  return ctx
}
