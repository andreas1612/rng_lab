import axios from 'axios'

// ── Type definitions ─────────────────────────────────────────────────────────

export type TestStatus = 'pass' | 'warning' | 'fail' | 'insufficient_data' | 'error'
export type OverallStatus = 'pass' | 'warning' | 'fail' | 'incomplete'

export interface NistTest {
  name: string
  p_value: number | null
  status: TestStatus
  threshold_used: number
  error_detail?: string
}

export interface Level2PerTest {
  name: string
  n_sequences: number
  n_passing: number
  proportion_passing: number | null
  proportion_result: 'pass' | 'warning' | 'fail' | 'insufficient_data'
  ks_p_value: number | null
  uniformity_result: 'pass' | 'fail' | 'insufficient_data' | 'error'
}

export interface Level2 {
  n_sequences: number
  per_test: Level2PerTest[]
  tests_proportion_pass: number
  tests_uniformity_pass: number
}

export interface SampleInfo {
  filename: string
  size_bits: number
  size_mb: number
  warnings: string[]
  sufficient: boolean
}

export interface NistResult {
  suite: string
  sample_info: SampleInfo
  tests: NistTest[]
  level2?: Level2
}

export interface JurisdictionScore {
  id: string
  name: string
  short_name: string
  overall: OverallStatus
  tests_passed: number
  tests_warning: number
  tests_failed: number
  tests_not_run: number
  nist_check: { result: string; detail: string }
  rtp_floor_check: { result: string; detail: string }
}

export interface SupplementaryTest {
  name: string
  statistic: number | null
  p_value: number | null
  status: TestStatus
  detail: string
}

export interface SupplementaryResult {
  suite: string
  tests: SupplementaryTest[]
  error?: string
}

export interface AnalysisResult {
  filename: string
  generated_at: string
  nist_result: NistResult
  supplementary_result: SupplementaryResult
  jurisdiction_scores: JurisdictionScore[]
}

// ── API functions ────────────────────────────────────────────────────────────

// Use relative URLs — Vite proxy rewrites /api/* → http://localhost:8081/*
const api = axios.create({ baseURL: '' })

export async function checkHealth(): Promise<{ status: string }> {
  const res = await api.get<{ status: string }>('/api/health')
  return res.data
}

export async function analyseFile(file: File): Promise<AnalysisResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post<AnalysisResult>('/api/analyse', form)
  return res.data
}

export async function generateReport(
  file: File,
  aupTimestamp: string,
  aupRef: string,
): Promise<Blob> {
  const form = new FormData()
  form.append('file', file)
  form.append('aup_timestamp', aupTimestamp)
  form.append('aup_ref', aupRef)
  const res = await api.post('/api/report', form, { responseType: 'blob' })
  return res.data as Blob
}
