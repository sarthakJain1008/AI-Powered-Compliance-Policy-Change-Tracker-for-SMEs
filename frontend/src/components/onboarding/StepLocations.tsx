/**
 * @module StepLocations
 * @description Step 4 — Where does the company operate?
 * Primary state (HQ), multi-select operating states, and export markets.
 */
'use client'

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { MapPin, Globe2, X } from 'lucide-react'
import { useOnboarding } from './OnboardingContext'
import { Button } from '@/components/ui/Button'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepLocations({ onNext, onBack }: Props) {
  const { state, updateStep4, options } = useOnboarding()
  const [error, setError] = useState('')

  const toggleOperatingState = (val: string) => {
    const current = state.step4.operating_states
    const updated = current.includes(val)
      ? current.filter((s) => s !== val)
      : [...current, val]
    updateStep4({ operating_states: updated })
  }

  const toggleExportMarket = (val: string) => {
    const current = state.step4.export_markets
    const updated = current.includes(val)
      ? current.filter((m) => m !== val)
      : [...current, val]
    updateStep4({ export_markets: updated })
  }

  const handleNext = () => {
    if (!state.step4.primary_state) {
      setError('Please select your primary (HQ) state.')
      return
    }
    setError('')
    onNext()
  }

  const primaryStateOption = options?.indian_states.find(
    (s) => s.value === state.step4.primary_state
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Where do you operate?</h2>
        <p className="mt-1 text-sm text-slate-500">
          Your state determines which state laws apply — Shops & Estb Act, state GST, and labour notifications.
        </p>
      </div>

      {/* Primary State (HQ) */}
      <div className="space-y-1.5">
        <label className="flex items-center gap-1.5 text-sm font-semibold text-slate-700">
          <MapPin className="h-4 w-4 text-brand-primary" />
          Primary State (Headquarters) *
        </label>
        <select
          value={state.step4.primary_state}
          onChange={(e) => {
            const opt = options?.indian_states.find((s) => s.value === e.target.value)
            updateStep4({
              primary_state: e.target.value,
              primary_jurisdiction_id: opt?.jurisdiction_id ?? null,
            })
            setError('')
          }}
          className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
        >
          <option value="">— Select your state —</option>
          {options?.indian_states.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>

      {/* Operating States — multi-select chip grid */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-700">
          Other States You Operate In
          <span className="ml-1 text-slate-400 font-normal">(optional — select all that apply)</span>
        </label>

        {/* Selected chips */}
        {state.step4.operating_states.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {state.step4.operating_states.map((val) => {
              const opt = options?.indian_states.find((s) => s.value === val)
              return (
                <span
                  key={val}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-brand-primary"
                >
                  {opt?.label ?? val}
                  <button
                    type="button"
                    onClick={() => toggleOperatingState(val)}
                    className="text-blue-400 hover:text-brand-primary"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )
            })}
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-52 overflow-y-auto rounded-lg border border-slate-200 p-2">
          {options?.indian_states
            .filter((s) => s.value !== state.step4.primary_state && s.value !== 'india')
            .map((s) => {
              const isSelected = state.step4.operating_states.includes(s.value)
              return (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => toggleOperatingState(s.value)}
                  className={clsx(
                    'rounded-lg px-2.5 py-1.5 text-xs font-medium text-left transition-all',
                    isSelected
                      ? 'bg-brand-primary text-white'
                      : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                  )}
                >
                  {s.label}
                </button>
              )
            })}
        </div>
      </div>

      {/* Exports Toggle */}
      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <input
          type="checkbox"
          id="exports_business"
          checked={state.step4.exports_business}
          onChange={(e) =>
            updateStep4({ exports_business: e.target.checked, export_markets: [] })
          }
          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
        />
        <div>
          <label htmlFor="exports_business" className="flex items-center gap-1.5 text-sm font-semibold text-slate-800 cursor-pointer">
            <Globe2 className="h-4 w-4 text-green-500" />
            We export products or services internationally
          </label>
          <p className="mt-0.5 text-xs text-slate-500">
            Triggers FEMA, DGFT IEC, GST refund, and GDPR obligations.
          </p>
        </div>
      </div>

      {/* Export Markets */}
      {state.step4.exports_business && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700">Export Markets</label>
          <div className="flex flex-wrap gap-2">
            {options?.export_markets.map((m) => {
              const isSelected = state.step4.export_markets.includes(m.value)
              return (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => toggleExportMarket(m.value)}
                  className={clsx(
                    'rounded-full border px-3 py-1 text-xs font-medium transition-all',
                    isSelected
                      ? 'border-green-400 bg-green-100 text-green-800'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-green-300'
                  )}
                >
                  {m.label}
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
          Review & Confirm →
        </Button>
      </div>
    </div>
  )
}
