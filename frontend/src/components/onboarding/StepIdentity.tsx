/**
 * @module StepIdentity
 * @description Step 1 — Business Identity: company name, entity type, incorporation year.
 */
'use client'

import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Building2, FileText, CalendarDays, Hash, Sparkles } from 'lucide-react'
import { useOnboarding } from './OnboardingContext'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

const schema = z.object({
  company_name:          z.string().min(2, 'Company name is required').max(200),
  entity_type:           z.string().min(1, 'Please select entity type'),
  year_of_incorporation: z.number().int().min(1900).max(2026).nullable().optional(),
  cin_llpin:             z.string().max(30).optional(),
  is_dpiit_startup:      z.boolean(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onNext: () => void
}

export function StepIdentity({ onNext }: Props) {
  const { state, updateStep1, options, isLoadingOptions } = useOnboarding()

  const { register, handleSubmit, watch, setValue, formState: { errors } } =
    useForm<FormValues>({
      resolver: zodResolver(schema),
      defaultValues: {
        company_name:          state.step1.company_name,
        entity_type:           state.step1.entity_type,
        year_of_incorporation: state.step1.year_of_incorporation ?? undefined,
        cin_llpin:             state.step1.cin_llpin,
        is_dpiit_startup:      state.step1.is_dpiit_startup,
      },
    })

  const isDPIIT = watch('is_dpiit_startup')

  const onSubmit = (values: FormValues) => {
    updateStep1({
      company_name:          values.company_name,
      entity_type:           values.entity_type,
      year_of_incorporation: values.year_of_incorporation ?? null,
      cin_llpin:             values.cin_llpin ?? '',
      is_dpiit_startup:      values.is_dpiit_startup,
    })
    onNext()
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Tell us about your business</h2>
        <p className="mt-1 text-sm text-slate-500">
          This helps us identify which laws and regulations apply to you.
        </p>
      </div>

      {/* Company Name */}
      <Input
        id="company_name"
        label="Company / Business Name *"
        placeholder="e.g. Acme Technologies Pvt. Ltd."
        leftIcon={<Building2 className="h-4 w-4" />}
        error={errors.company_name?.message}
        {...register('company_name')}
      />

      {/* Entity Type */}
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-slate-700">
          Business Entity Type *
        </label>
        {isLoadingOptions ? (
          <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
        ) : (
          <select
            {...register('entity_type')}
            className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
          >
            <option value="">— Select entity type —</option>
            {options?.entity_types.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )}
        {errors.entity_type && (
          <p className="text-xs text-red-600">{errors.entity_type.message}</p>
        )}
      </div>

      {/* Incorporation Year */}
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-slate-700">
          Year of Incorporation
          <span className="ml-1 text-slate-400 font-normal">(optional)</span>
        </label>
        {isLoadingOptions ? (
          <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
        ) : (
          <select
            {...register('year_of_incorporation', { valueAsNumber: true })}
            className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
          >
            <option value="">— Select year —</option>
            {options?.incorporation_years.map((yr) => (
              <option key={yr} value={yr}>{yr}</option>
            ))}
          </select>
        )}
      </div>

      {/* CIN / LLPIN */}
      <Input
        id="cin_llpin"
        label="CIN / LLPIN"
        placeholder="e.g. U72900MH2022PTC123456"
        leftIcon={<Hash className="h-4 w-4" />}
        helperText="Ministry of Corporate Affairs identifier (optional)"
        {...register('cin_llpin')}
      />

      {/* DPIIT Startup Toggle */}
      <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
        <div className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center">
          <input
            type="checkbox"
            id="is_dpiit_startup"
            checked={isDPIIT}
            onChange={(e) => setValue('is_dpiit_startup', e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
          />
        </div>
        <div>
          <label
            htmlFor="is_dpiit_startup"
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-800 cursor-pointer"
          >
            <Sparkles className="h-4 w-4 text-brand-primary" />
            DPIIT Recognised Startup
          </label>
          <p className="mt-0.5 text-xs text-slate-500">
            Eligible for startup tax exemptions, simplified compliances, and self-certification benefits.
          </p>
        </div>
      </div>

      <Button type="submit" fullWidth>
        Continue →
      </Button>
    </form>
  )
}
