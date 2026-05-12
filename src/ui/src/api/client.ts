import axios from 'axios'

// ── Label scheme (mirrors core/labels.py) ────────────────────────────────────

export type TestStatus =
  | 'PASS'
  | 'BORDERLINE'
  | 'FAIL'
  | 'NOT_RUN'
  | 'INDICATIVE_ONLY'
  | 'INCONCLUSIVE'

export type OverallStatus = 'PASS' | 'BORDERLINE' | 'FAIL' | 'incomplete'

// ── Interfaces ───────────────────────────────────────────────────────────────

export interface NistTest {
  test_id: string
  name: string
  statistic: number | null
  p_value: number | null
  status: TestStatus
  detail: string
}

export interface Level2PerTest {
  test_id: string
  name: string
  n_sequences: number
  n_passing: number
  proportion_passing: number | null
  proportion_result: TestStatus
  ks_p_value: number | null
  uniformity_result: TestStatus
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
  overall: string
  tests_passed: number
  tests_borderline: number
  tests_warning: number   // legacy alias — same value as tests_borderline
  tests_failed: number
  tests_not_run: number
  nist_check: { result: string; detail: string }
  rtp_floor_check: { result: string; detail: string }
  notes?: string
}

export interface SupplementaryTest {
  test_id?: string
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

export interface AupRecord {
  accepted: boolean
  accepted_by: string
  acceptance_timestamp_utc: string
  aup_version: string
  aup_reference_id: string
}

export interface AnalysisResult {
  report_id: string
  tool_version: string
  methodology_version: string
  filename: string
  input_sha256: string
  input_size_bytes: number
  input_size_bits: number
  generated_at: string
  aup: AupRecord
  nist_result: NistResult
  supplementary_result: SupplementaryResult
  jurisdiction_scores: JurisdictionScore[]
}

// ── AUP payload ──────────────────────────────────────────────────────────────

export interface AupFields {
  accepted: boolean
  acceptedBy: string
  timestamp: string
  version: string
  referenceId: string
}

// ── API functions ────────────────────────────────────────────────────────────

const api = axios.create({ baseURL: '' })

export async function checkHealth(): Promise<{ status: string; tool_version?: string }> {
  const res = await api.get<{ status: string; tool_version?: string }>('/api/health')
  return res.data
}

export async function analyseFile(file: File, aup: AupFields): Promise<AnalysisResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('aup_accepted', String(aup.accepted))
  form.append('aup_accepted_by', aup.acceptedBy)
  form.append('aup_acceptance_timestamp', aup.timestamp)
  form.append('aup_version_field', aup.version)
  form.append('aup_reference_id', aup.referenceId)
  const res = await api.post<AnalysisResult>('/api/analyse', form)
  return res.data
}

export async function generateReport(file: File, aup: AupFields): Promise<Blob> {
  const form = new FormData()
  form.append('file', file)
  form.append('aup_accepted', String(aup.accepted))
  form.append('aup_accepted_by', aup.acceptedBy)
  form.append('aup_acceptance_timestamp', aup.timestamp)
  form.append('aup_version_field', aup.version)
  form.append('aup_reference_id', aup.referenceId)
  const res = await api.post('/api/report', form, { responseType: 'blob' })
  return res.data as Blob
}
