/**
 * @module StepSize
 * @description Step 3 — Team & Revenue: employee range, turnover range, funding stage.
 * Each dropdown also shows the compliance implications of each selection.
 */
'use client'

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Users, TrendingUp, Banknote, Info } from 'lucide-react'
import { useOnboarding } from './OnboardingContext'
import { Button } from '@/components/ui/Button'

interface Props {
  onNext: () => void
  onBack: () => void
}

function OptionCard({
  value,
  label,
  note,
  selected,
  onClick,
}: {
  value: string
  label: string
  note?: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex flex-col items-start gap-1 rounded-xl border-2 p-3.5 text-left transition-all duration-150 w-full',
        selected
          ? 'border-brand-primary bg-blue-50 shadow-sm shadow-blue-100'
          : 'border-slate-200 bg-white hover:border-slate-300'
      )}
    >
      <span className={clsx('text-sm font-semibold', selected ? 'text-brand-primary' : 'text-slate-700')}>
        {label}
      </span>
      {note && (
        <span className="flex items-start gap-1 text-[11px] text-slate-400 leading-snug">
          <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
          {note}
        </span>
      )}
    </button>
  )
}

export function StepSize({ onNext, onBack }: Props) {
  const { state, updateStep3, options } = useOnboarding()
  const [error, setError] = useState('')

  const handleNext = () => {
    if (!state.step3.employee_range || !state.step3.turnover_range) {
      setError('Please select both employee count and annual turnover.')
      return
    }
    setError('')
    onNext()
  }

  return (
    <div className="space-y-7">
      <div>
        <h2 className="text-xl font-bold text-slate-900">How big is your team?</h2>
        <p className="mt-1 text-sm text-slate-500">
          Employee count and turnover determine which labour laws and tax regulations apply.
        </p>
      </div>

      {/* Employee Range */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Users className="h-4 w-4 text-brand-primary" />
          Number of Employees *
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {options?.employee_ranges.map((opt) => (
            <OptionCard
              key={opt.value}
              value={opt.value}
              label={opt.label}
              note={opt.note}
              selected={state.step3.employee_range === opt.value}
              onClick={() => { updateStep3({ employee_range: opt.value }); setError('') }}
            />
          ))}
        </div>
      </div>

      {/* Turnover Range */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <TrendingUp className="h-4 w-4 text-brand-primary" />
          Annual Turnover (₹) *
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {options?.turnover_ranges.map((opt) => (
            <OptionCard
              key={opt.value}
              value={opt.value}
              label={opt.label}
              note={opt.note}
              selected={state.step3.turnover_range === opt.value}
              onClick={() => { updateStep3({ turnover_range: opt.value }); setError('') }}
            />
          ))}
        </div>
      </div>

      {/* Funding Stage */}
      <div className="space-y-1.5">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Banknote className="h-4 w-4 text-slate-400" />
          Funding Stage
          <span className="text-slate-400 font-normal">(optional)</span>
        </label>
        <select
          value={state.step3.funding_stage}
          onChange={(e) => updateStep3({ funding_stage: e.target.value })}
          className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
        >
          <option value="">— Select funding stage —</option>
          {options?.funding_stages.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <p className="text-xs text-slate-400">Helps identify FEMA, SEBI, and RBI reporting obligations.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onBack} className="flex-1">
          ← Back
        </Button>
        <Button type="button" onClick={handleNext} className="flex-1">
          Continue →
        </Button>
      </div>
    </div>
  )
}
