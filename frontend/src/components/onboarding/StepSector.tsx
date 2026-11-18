/**
 * @module StepSector
 * @description Step 2 — Business Category: sector card grid + conditional sub-type dropdown.
 */
'use client'

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Rocket } from 'lucide-react'
import { useOnboarding } from './OnboardingContext'
import { Button } from '@/components/ui/Button'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepSector({ onNext, onBack }: Props) {
  const { state, updateStep2, options, isLoadingOptions } = useOnboarding()
  const [error, setError] = useState('')

  const selectedSectorId = state.step2.primary_sector_id

  const subTypes = selectedSectorId
    ? (options?.sector_sub_types[selectedSectorId] ?? [])
    : []

  const handleSectorSelect = (sectorId: number, sectorName: string) => {
    updateStep2({
      primary_sector_id:   sectorId,
      primary_sector_name: sectorName,
      business_sub_type:   '',  // reset sub-type when sector changes
    })
    setError('')
  }

  const handleNext = () => {
    if (!state.step2.primary_sector_id) {
      setError('Please select your primary business sector.')
      return
    }
    onNext()
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">What type of business are you?</h2>
        <p className="mt-1 text-sm text-slate-500">
          Select the sector that best describes your primary activity.
        </p>
      </div>

      {/* Sector Card Grid */}
      {isLoadingOptions ? (
        <div className="grid grid-cols-3 gap-3">
          {[...Array(15)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {options?.sectors.map((sector) => {
            const isSelected = selectedSectorId === sector.sector_id
            return (
              <button
                key={sector.sector_id}
                type="button"
                onClick={() => handleSectorSelect(sector.sector_id, sector.name)}
                className={clsx(
                  'relative flex flex-col items-start gap-1.5 rounded-xl border-2 p-3.5 text-left transition-all duration-150',
                  isSelected
                    ? 'border-brand-primary bg-blue-50 shadow-md shadow-blue-100'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                )}
              >
                <span className="text-2xl leading-none">{sector.icon}</span>
                <span className={clsx(
                  'text-xs font-semibold leading-tight',
                  isSelected ? 'text-brand-primary' : 'text-slate-700'
                )}>
                  {sector.name}
                </span>
                {isSelected && (
                  <div className="absolute top-2 right-2 h-2 w-2 rounded-full bg-brand-primary" />
                )}
              </button>
            )
          })}
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Conditional Sub-type Dropdown */}
      {selectedSectorId && subTypes.length > 0 && (
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-slate-700">
            Business Sub-type
            <span className="ml-1 text-slate-400 font-normal">(optional but recommended)</span>
          </label>
          <select
            value={state.step2.business_sub_type}
            onChange={(e) => updateStep2({ business_sub_type: e.target.value })}
            className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
          >
            <option value="">— Select sub-type —</option>
            {subTypes.map((sub) => (
              <option key={sub.value} value={sub.value}>{sub.label}</option>
            ))}
          </select>
          <p className="text-xs text-slate-400">
            Helps us pinpoint sector-specific regulators (e.g. RBI for fintech, FSSAI for food).
          </p>
        </div>
      )}

      {/* Is Startup Toggle */}
      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <input
          type="checkbox"
          id="is_startup"
          checked={state.step2.is_startup}
          onChange={(e) => updateStep2({ is_startup: e.target.checked, startup_stage: '' })}
          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
        />
        <div>
          <label htmlFor="is_startup" className="flex items-center gap-1.5 text-sm font-semibold text-slate-800 cursor-pointer">
            <Rocket className="h-4 w-4 text-purple-500" />
            This is a startup / early-stage company
          </label>
          <p className="mt-0.5 text-xs text-slate-500">
            Unlocks startup-specific regulatory exemptions and DPIIT benefits.
          </p>
        </div>
      </div>

      {/* Conditional Startup Stage */}
      {state.step2.is_startup && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700">Startup Stage *</label>
          <div className="grid grid-cols-1 gap-2">
            {options?.startup_stages.map((stage) => {
              const isSelected = state.step2.startup_stage === stage.value
              return (
                <button
                  key={stage.value}
                  type="button"
                  onClick={() => updateStep2({ startup_stage: stage.value })}
                  className={clsx(
                    'flex items-start gap-3 rounded-lg border-2 p-3 text-left transition-all',
                    isSelected
                      ? 'border-purple-400 bg-purple-50'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  )}
                >
                  <div className={clsx(
                    'mt-0.5 h-4 w-4 flex-shrink-0 rounded-full border-2',
                    isSelected ? 'border-purple-500 bg-purple-500' : 'border-slate-300'
                  )} />
                  <div>
                    <p className={clsx('text-sm font-semibold', isSelected ? 'text-purple-800' : 'text-slate-700')}>
                      {stage.label}
                    </p>
                    {stage.description && (
                      <p className="text-xs text-slate-400 mt-0.5">{stage.description}</p>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

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
