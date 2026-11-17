/**
 * @module onboardingApi
 * @description Typed API functions for the onboarding wizard.
 */

import api from '@/lib/api'

// ─── Types (mirror backend schemas) ──────────────────────────────────────────

export interface DropdownOption {
  value: string
  label: string
  note?: string
  description?: string
  icon?: string
  sector_id?: number
  nic_code?: string
  jurisdiction_id?: number
}

export interface SectorOption {
  sector_id: number
  name: string
  icon: string
  nic_code: string
  description: string
}

export interface OnboardingOptions {
  entity_types: DropdownOption[]
  sectors: SectorOption[]
  sector_sub_types: Record<number, DropdownOption[]>
  startup_stages: DropdownOption[]
  employee_ranges: DropdownOption[]
  turnover_ranges: DropdownOption[]
  funding_stages: DropdownOption[]
  indian_states: (DropdownOption & { jurisdiction_id: number })[]
  export_markets: DropdownOption[]
  incorporation_years: number[]
}

export interface OnboardingSubmitPayload {
  step1: {
    company_name: string
    entity_type: string
    year_of_incorporation: number | null
    cin_llpin: string | null
    is_dpiit_startup: boolean
  }
  step2: {
    primary_sector_id: number
    primary_sector_name: string
    business_sub_type: string | null
    is_startup: boolean
    startup_stage: string | null
  }
  step3: {
    employee_range: string
    turnover_range: string
    funding_stage: string | null
  }
  step4: {
    primary_state: string
    primary_jurisdiction_id: number | null
    operating_states: string[]
    exports_business: boolean
    export_markets: string[]
  }
}

export interface OnboardingStatus {
  is_onboarded: boolean
  has_profile: boolean
}

// ─── API Functions ────────────────────────────────────────────────────────────

export const onboardingApi = {
  async getOptions(): Promise<OnboardingOptions> {
    const { data } = await api.get<OnboardingOptions>('/onboarding/options')
    return data
  },

  async getStatus(): Promise<OnboardingStatus> {
    const { data } = await api.get<OnboardingStatus>('/onboarding/status')
    return data
  },

  async submit(payload: OnboardingSubmitPayload) {
    const { data } = await api.post('/onboarding/submit', payload)
    return data
  },

  async getProfile() {
    const { data } = await api.get('/onboarding/profile')
    return data
  },
}
