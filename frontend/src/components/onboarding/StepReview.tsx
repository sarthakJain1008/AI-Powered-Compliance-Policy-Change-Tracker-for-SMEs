/**
 * @module StepReview
 * @description Step 5 — Review & Confirm: summary card with edit links and final submit.
 */
'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Building2, ChevronRight, Users, TrendingUp, MapPin, Briefcase,
  CheckCircle2, AlertCircle, Edit2, Rocket, Globe2
} from 'lucide-react'
import { useOnboarding } from './OnboardingContext'
import { onboardingApi } from '@/lib/onboardingApi'
import { Button } from '@/components/ui/Button'

interface Props {
  onBack: () => void
  onEditStep: (step: number) => void
}

function ReviewRow({
  icon,
  label,
  value,
  onEdit,
}: {
  icon: React.ReactNode
  label: string
  value: string | React.ReactNode
  onEdit: () => void
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-3 border-b border-slate-100 last:border-0">
      <div className="flex items-start gap-2.5 min-w-0">
        <span className="mt-0.5 text-slate-400 flex-shrink-0">{icon}</span>
        <div className="min-w-0">
          <p className="text-xs text-slate-400 font-medium">{label}</p>
          <div className="text-sm font-semibold text-slate-800 break-words">{value}</div>
        </div>
      </div>
      <button
        type="button"
        onClick={onEdit}
        className="flex-shrink-0 flex items-center gap-1 text-xs text-brand-primary hover:text-brand-secondary font-medium"
      >
        <Edit2 className="h-3 w-3" /> Edit
      </button>
    </div>
  )
}

export function StepReview({ onBack, onEditStep }: Props) {
  const router = useRouter()
  const { state, options } = useOnboarding()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const entityLabel = options?.entity_types.find(
    (e) => e.value === state.step1.entity_type
  )?.label ?? state.step1.entity_type

  const sectorLabel = state.step2.primary_sector_name

  const subTypeLabel = options?.sector_sub_types[state.step2.primary_sector_id ?? 0]?.find(
    (s) => s.value === state.step2.business_sub_type
  )?.label

  const startupStageLabel = options?.startup_stages.find(
    (s) => s.value === state.step2.startup_stage
  )?.label

  const employeeLabel = options?.employee_ranges.find(
    (e) => e.value === state.step3.employee_range
  )?.label

  const turnoverLabel = options?.turnover_ranges.find(
    (t) => t.value === state.step3.turnover_range
  )?.label

  const fundingLabel = options?.funding_stages.find(
    (f) => f.value === state.step3.funding_stage
  )?.label

  const primaryStateLabel = options?.indian_states.find(
    (s) => s.value === state.step4.primary_state
  )?.label

  const operatingStateLabels = state.step4.operating_states
    .map((v) => options?.indian_states.find((s) => s.value === v)?.label ?? v)
    .join(', ')

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setServerError(null)
    try {
      const payload = {
        step1: {
          company_name:          state.step1.company_name,
          entity_type:           state.step1.entity_type,
          year_of_incorporation: state.step1.year_of_incorporation,
          cin_llpin:             state.step1.cin_llpin || null,
          is_dpiit_startup:      state.step1.is_dpiit_startup,
        },
        step2: {
          primary_sector_id:   state.step2.primary_sector_id!,
          primary_sector_name: state.step2.primary_sector_name,
          business_sub_type:   state.step2.business_sub_type || null,
          is_startup:          state.step2.is_startup,
          startup_stage:       state.step2.startup_stage || null,
        },
        step3: {
          employee_range: state.step3.employee_range,
          turnover_range: state.step3.turnover_range,
          funding_stage:  state.step3.funding_stage || null,
        },
        step4: {
          primary_state:          state.step4.primary_state,
          primary_jurisdiction_id: state.step4.primary_jurisdiction_id,
          operating_states:       state.step4.operating_states,
          exports_business:       state.step4.exports_business,
          export_markets:         state.step4.export_markets,
        },
      }
      await onboardingApi.submit(payload)
      router.replace('/dashboard')
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const e = err as { response?: { data?: { detail?: string } } }
        setServerError(e.response?.data?.detail ?? 'Failed to save profile. Please try again.')
      } else {
        setServerError('An unexpected error occurred.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Review your profile</h2>
        <p className="mt-1 text-sm text-slate-500">
          Confirm your details before we personalise your compliance calendar.
        </p>
      </div>

      {serverError && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0 text-red-500" />
          {serverError}
        </div>
      )}

      {/* Summary Card */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm divide-y divide-slate-100">
        <div className="px-4 py-3 bg-slate-50 rounded-t-xl">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Step 1 — Business Identity
          </p>
        </div>
        <div className="px-4">
          <ReviewRow icon={<Building2 className="h-4 w-4" />} label="Company Name"
            value={state.step1.company_name} onEdit={() => onEditStep(1)} />
          <ReviewRow icon={<Briefcase className="h-4 w-4" />} label="Entity Type"
            value={entityLabel} onEdit={() => onEditStep(1)} />
          {state.step1.year_of_incorporation && (
            <ReviewRow icon={<ChevronRight className="h-4 w-4" />} label="Year of Incorporation"
              value={String(state.step1.year_of_incorporation)} onEdit={() => onEditStep(1)} />
          )}
          {state.step1.is_dpiit_startup && (
            <ReviewRow icon={<CheckCircle2 className="h-4 w-4 text-brand-primary" />}
              label="DPIIT Startup" value="✅ Recognised Startup" onEdit={() => onEditStep(1)} />
          )}
        </div>

        <div className="px-4 py-3 bg-slate-50">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Step 2 — Business Category
          </p>
        </div>
        <div className="px-4">
          <ReviewRow icon={<Briefcase className="h-4 w-4" />} label="Primary Sector"
            value={sectorLabel} onEdit={() => onEditStep(2)} />
          {subTypeLabel && (
            <ReviewRow icon={<ChevronRight className="h-4 w-4" />} label="Sub-type"
              value={subTypeLabel} onEdit={() => onEditStep(2)} />
          )}
          {state.step2.is_startup && startupStageLabel && (
            <ReviewRow icon={<Rocket className="h-4 w-4 text-purple-500" />}
              label="Startup Stage" value={startupStageLabel} onEdit={() => onEditStep(2)} />
          )}
        </div>

        <div className="px-4 py-3 bg-slate-50">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Step 3 — Team & Revenue
          </p>
        </div>
        <div className="px-4">
          <ReviewRow icon={<Users className="h-4 w-4" />} label="Employees"
            value={employeeLabel ?? '—'} onEdit={() => onEditStep(3)} />
          <ReviewRow icon={<TrendingUp className="h-4 w-4" />} label="Annual Turnover"
            value={turnoverLabel ?? '—'} onEdit={() => onEditStep(3)} />
          {fundingLabel && (
            <ReviewRow icon={<ChevronRight className="h-4 w-4" />} label="Funding Stage"
              value={fundingLabel} onEdit={() => onEditStep(3)} />
          )}
        </div>

        <div className="px-4 py-3 bg-slate-50">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Step 4 — Locations
          </p>
        </div>
        <div className="px-4">
          <ReviewRow icon={<MapPin className="h-4 w-4" />} label="HQ State"
            value={primaryStateLabel ?? '—'} onEdit={() => onEditStep(4)} />
          {operatingStateLabels && (
            <ReviewRow icon={<MapPin className="h-4 w-4" />} label="Operating States"
              value={operatingStateLabels} onEdit={() => onEditStep(4)} />
          )}
          {state.step4.exports_business && (
            <ReviewRow icon={<Globe2 className="h-4 w-4 text-green-500" />}
              label="Exports" value={`✅ International exports`} onEdit={() => onEditStep(4)} />
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <Button type="button" variant="secondary" onClick={onBack} className="flex-1">
          ← Back
        </Button>
        <Button type="button" onClick={handleSubmit} isLoading={isSubmitting} className="flex-1">
          Complete Setup 🚀
        </Button>
      </div>
    </div>
  )
}
