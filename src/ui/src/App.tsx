import { useEffect, useRef, useState } from 'react'
import {
  checkHealth,
  analyseFile,
  generateReport,
  AnalysisResult,
  AupFields,
  JurisdictionScore,
  NistTest,
  SupplementaryTest,
} from './api/client'

// ── Constants ────────────────────────────────────────────────────────────────

const MIN_BYTES       = 125_000        // 1M bits
const MULTI_SEQ_BYTES = 12_500_000     // 100M bits
const AUP_VERSION     = 'AUP-v0.1'

// ── 6-label colour palette ───────────────────────────────────────────────────
// Mirrors core/labels.py label scheme. Keys are the exact strings the backend emits.

const STATUS_COLOURS: Record<string, { bg: string; fg: string; border: string }> = {
  PASS:            { bg: '#d4edda', fg: '#155724', border: '#c3e6cb' },
  BORDERLINE:      { bg: '#ffe5b4', fg: '#7a4a00', border: '#ffcd6e' },
  FAIL:            { bg: '#f8d7da', fg: '#842029', border: '#f5c6cb' },
  INDICATIVE_ONLY: { bg: '#cce5ff', fg: '#004085', border: '#b8daff' },
  INCONCLUSIVE:    { bg: '#e9ecef', fg: '#6c757d', border: '#dee2e6' },
  NOT_RUN:         { bg: '#e9ecef', fg: '#6c757d', border: '#dee2e6' },
  // Lowercase fallbacks for jurisdiction sub-result strings
  incomplete:      { bg: '#e9ecef', fg: '#6c757d', border: '#dee2e6' },
  not_applicable:  { bg: '#e9ecef', fg: '#6c757d', border: '#dee2e6' },
  pass:            { bg: '#d4edda', fg: '#155724', border: '#c3e6cb' },
  fail:            { bg: '#f8d7da', fg: '#842029', border: '#f5c6cb' },
}

function Badge({ status, label }: { status: string; label?: string }) {
  const c = STATUS_COLOURS[status] ?? STATUS_COLOURS.INCONCLUSIVE
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 3,
      fontSize: '0.75rem',
      fontWeight: 700,
      background: c.bg,
      color: c.fg,
      border: `1px solid ${c.border}`,
      letterSpacing: '0.03em',
    }}>
      {label ?? status}
    </span>
  )
}

// ── Size validation ──────────────────────────────────────────────────────────

function sizeMessage(bytes: number): { kind: 'error' | 'warning' | 'info' | null; text: string } {
  if (bytes === 0)
    return { kind: 'error', text: 'File is empty — select a valid RNG output file.' }
  if (bytes < MIN_BYTES)
    return {
      kind: 'warning',
      text: `File is ${(bytes / 1024).toFixed(1)} KB (${(bytes * 8).toLocaleString()} bits) — below the 1,000,000-bit minimum. Results will be marked INDICATIVE_ONLY.`,
    }
  if (bytes < MULTI_SEQ_BYTES)
    return {
      kind: 'info',
      text: `For multi-sequence Level-2 analysis, provide at least 100,000,000 bits (12.5 MB). Current: ${(bytes / 1024 / 1024).toFixed(2)} MB.`,
    }
  return { kind: null, text: '' }
}

// ── Sub-components ───────────────────────────────────────────────────────────

function SizeAlert({ bytes }: { bytes: number }) {
  const { kind, text } = sizeMessage(bytes)
  if (!kind) return null
  const colours = {
    error:   { bg: '#f8d7da', border: '#f5c6cb', fg: '#842029' },
    warning: { bg: '#fff3cd', border: '#ffeeba', fg: '#856404' },
    info:    { bg: '#d1ecf1', border: '#bee5eb', fg: '#0c5460' },
  }
  const c = colours[kind]
  return (
    <div style={{
      background: c.bg, border: `1px solid ${c.border}`, borderRadius: 4,
      padding: '0.5rem 0.75rem', fontSize: '0.8rem', color: c.fg, marginTop: '0.5rem',
    }}>
      {kind === 'error' ? '✕' : kind === 'warning' ? '⚠' : 'ℹ'} {text}
    </div>
  )
}

function JurisdictionRow({ jur }: { jur: JurisdictionScore }) {
  const borderline = jur.tests_borderline ?? jur.tests_warning ?? 0
  return (
    <div style={{
      border: '1px solid #dee2e6', borderRadius: 4, padding: '0.75rem 1rem',
      marginBottom: '0.5rem', background: '#fff',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
        <strong style={{ fontSize: '0.95rem', flex: 1 }}>{jur.name} ({jur.short_name})</strong>
        <Badge status={jur.overall} />
      </div>
      <div style={{ fontSize: '0.8rem', color: '#555', lineHeight: 1.6 }}>
        <div><strong>NIST:</strong> {jur.nist_check.detail}</div>
        <div><strong>RTP:</strong> {jur.rtp_floor_check.detail}</div>
        <div>
          <strong>Tests:</strong>{' '}
          {jur.tests_passed} PASS · {borderline} BORDERLINE · {jur.tests_failed} FAIL · {jur.tests_not_run} NOT_RUN
        </div>
      </div>
    </div>
  )
}

function NistRow({ test }: { test: NistTest }) {
  const p = test.p_value
  return (
    <tr>
      <td style={{ padding: '4px 8px', fontSize: '0.8rem' }}>{test.name}</td>
      <td style={{ padding: '4px 8px', fontSize: '0.8rem', fontFamily: 'monospace' }}>
        {p !== null ? p.toFixed(6) : '—'}
      </td>
      <td style={{ padding: '4px 8px' }}><Badge status={test.status} /></td>
      <td style={{ padding: '4px 8px', fontSize: '0.75rem', color: '#666' }}>{test.detail}</td>
    </tr>
  )
}

function SuppRow({ test }: { test: SupplementaryTest }) {
  return (
    <tr>
      <td style={{ padding: '4px 8px', fontSize: '0.8rem' }}>{test.name}</td>
      <td style={{ padding: '4px 8px', fontSize: '0.8rem', fontFamily: 'monospace' }}>
        {test.statistic !== null ? test.statistic.toFixed(6) : '—'}
      </td>
      <td style={{ padding: '4px 8px', fontSize: '0.8rem', fontFamily: 'monospace' }}>
        {test.p_value !== null ? test.p_value.toFixed(6) : '—'}
      </td>
      <td style={{ padding: '4px 8px' }}><Badge status={test.status} /></td>
      <td style={{ padding: '4px 8px', fontSize: '0.75rem', color: '#555', maxWidth: 260 }}>{test.detail}</td>
    </tr>
  )
}

function CollapsibleSection({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ marginTop: '1rem' }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          background: 'none', border: 'none', padding: 0, cursor: 'pointer',
          fontWeight: 600, fontSize: '0.9rem', color: '#1a1a1a',
          display: 'flex', alignItems: 'center', gap: '0.4rem',
        }}
      >
        <span style={{ fontSize: '0.75rem' }}>{open ? '▼' : '▶'}</span>
        {title}
      </button>
      {open && <div style={{ marginTop: '0.5rem' }}>{children}</div>}
    </div>
  )
}

function TableWrap({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        {children}
      </table>
    </div>
  )
}

function Th({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <th style={{
      padding: '4px 8px', textAlign: 'left', fontSize: '0.8rem',
      background: '#eeeeee', borderBottom: '1px solid #ccc', ...style,
    }}>
      {children}
    </th>
  )
}

function InputField({
  label, value, onChange, placeholder, disabled,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  disabled?: boolean
}) {
  return (
    <div style={{ marginTop: '0.6rem' }}>
      <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.2rem' }}>
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        style={{
          width: '100%', boxSizing: 'border-box',
          padding: '0.35rem 0.5rem', fontSize: '0.85rem',
          border: '1px solid #ccc', borderRadius: 3,
          background: disabled ? '#f8f8f8' : '#fff',
          fontFamily: 'inherit',
        }}
      />
    </div>
  )
}

function MonoValue({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginBottom: '0.25rem', fontSize: '0.8rem' }}>
      <span style={{ color: '#555', marginRight: '0.4rem' }}>{label}</span>
      <code style={{ fontSize: '0.78rem', background: '#f4f4f4', padding: '1px 5px', borderRadius: 2, wordBreak: 'break-all' }}>
        {value}
      </code>
    </div>
  )
}

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'offline'>('checking')
  const [file, setFile] = useState<File | null>(null)

  // AUP fields
  const [aupChecked, setAupChecked]       = useState(false)
  const [aupTimestamp, setAupTimestamp]   = useState<string>('')
  const [aupAcceptedBy, setAupAcceptedBy] = useState('')
  const [aupVersion, setAupVersion]       = useState(AUP_VERSION)
  const [aupRefId, setAupRefId]           = useState('')

  const [loading, setLoading]             = useState(false)
  const [reportLoading, setReportLoading] = useState(false)
  const [result, setResult]               = useState<AnalysisResult | null>(null)
  const [error, setError]                 = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    checkHealth()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('offline'))
  }, [])

  function buildAup(): AupFields {
    return {
      accepted:    aupChecked,
      acceptedBy:  aupAcceptedBy || 'Not recorded',
      timestamp:   aupTimestamp  || new Date().toISOString(),
      version:     aupVersion    || AUP_VERSION,
      referenceId: aupRefId      || `web-ui-${Date.now()}`,
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    setFile(f)
    setResult(null)
    setError(null)
  }

  function handleAupChange(e: React.ChangeEvent<HTMLInputElement>) {
    const checked = e.target.checked
    setAupChecked(checked)
    setAupTimestamp(checked ? new Date().toISOString() : '')
  }

  async function handleRunAnalysis() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyseFile(file, buildAup())
      setResult(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Analysis failed — is the engine running on port 8081?')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerateReport() {
    if (!file || !aupChecked) return
    setReportLoading(true)
    try {
      const blob = await generateReport(file, buildAup())
      const reportId = result?.report_id ?? 'report'
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportId}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Report generation failed.')
    } finally {
      setReportLoading(false)
    }
  }

  const canRun = !!file && aupChecked && !loading && file.size > 0

  return (
    <div style={{ fontFamily: 'Georgia, Times, serif', color: '#1a1a1a', minHeight: '100vh', background: '#f8f9fa' }}>

      {/* Non-dismissable disclaimer banner */}
      <div style={{
        background: '#1a1a1a', color: '#fff', textAlign: 'center',
        padding: '0.5rem 1rem', fontSize: '0.78rem', letterSpacing: '0.04em',
      }}>
        PRE-AUDIT READINESS TOOL — NOT AN ACCREDITED AUDIT.
        Results cannot be submitted to any regulatory authority.
      </div>

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '2rem 1rem' }}>

        {/* Header */}
        <header style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 700, margin: '0 0 0.25rem' }}>
            MiniLab RNG Engine
          </h1>
          <p style={{ margin: 0, color: '#555', fontSize: '0.9rem', fontStyle: 'italic' }}>
            Pre-Audit Readiness Assessment — Not an Accredited Audit
          </p>
          <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{
              display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
              background: apiStatus === 'ok' ? '#155724' : apiStatus === 'offline' ? '#842029' : '#888',
            }} />
            <span style={{ color: '#555' }}>
              {apiStatus === 'checking' ? 'Checking engine…'
                : apiStatus === 'ok'      ? 'Engine online (localhost:8081)'
                : 'Engine offline — start: python -m uvicorn main:app --port 8081'}
            </span>
          </div>
        </header>

        {/* Upload + AUP card */}
        <div style={{
          background: '#fff', border: '1px solid #dee2e6', borderRadius: 6,
          padding: '1.5rem', marginBottom: '1.5rem',
        }}>
          <h2 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 700 }}>
            Upload RNG Binary File
          </h2>

          <input
            ref={fileInputRef}
            type="file"
            accept=".bin,.rng,.dat,.raw"
            onChange={handleFileChange}
            style={{ display: 'block', marginBottom: '0.5rem' }}
          />

          {file && (
            <div style={{ fontSize: '0.85rem', color: '#444', marginTop: '0.25rem' }}>
              <strong>{file.name}</strong>
              {' — '}
              {(file.size / 1024).toFixed(1)} KB ({(file.size * 8).toLocaleString()} bits)
            </div>
          )}

          {file && <SizeAlert bytes={file.size} />}

          {/* AUP section */}
          <div style={{
            marginTop: '1.25rem', background: '#f9f9f9',
            border: '1px solid #e0e0e0', borderRadius: 4, padding: '1rem',
          }}>
            <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', fontWeight: 700 }}>
              Acceptable Use Policy
            </h3>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <input
                id="aup"
                type="checkbox"
                checked={aupChecked}
                onChange={handleAupChange}
                style={{ marginTop: 3, flexShrink: 0 }}
              />
              <label htmlFor="aup" style={{ fontSize: '0.85rem', cursor: 'pointer' }}>
                I have read and agree to the <strong>MiniLab Acceptable Use Policy ({AUP_VERSION})</strong>.
                This tool is not an accredited audit and results cannot be used for regulatory submissions.
              </label>
            </div>

            {aupChecked && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                <InputField
                  label="Accepted by (name / organisation) *"
                  value={aupAcceptedBy}
                  onChange={setAupAcceptedBy}
                  placeholder="e.g. Jane Smith, Acme Ltd"
                />
                <InputField
                  label="Acceptance timestamp (UTC)"
                  value={aupTimestamp}
                  onChange={setAupTimestamp}
                  disabled
                />
                <InputField
                  label="AUP version"
                  value={aupVersion}
                  onChange={setAupVersion}
                />
                <InputField
                  label="Reference / job ID (optional)"
                  value={aupRefId}
                  onChange={setAupRefId}
                  placeholder="e.g. PROJ-001"
                />
              </div>
            )}
          </div>

          <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              onClick={handleRunAnalysis}
              disabled={!canRun}
              style={{
                background: canRun ? '#155724' : '#aaa', color: '#fff',
                border: 'none', borderRadius: 4, padding: '0.5rem 1.25rem',
                fontFamily: 'inherit', fontSize: '0.9rem',
                cursor: canRun ? 'pointer' : 'default', fontWeight: 600,
              }}
            >
              {loading ? 'Analysing…' : 'Run Analysis'}
            </button>

            {result && (
              <button
                onClick={handleGenerateReport}
                disabled={reportLoading || !aupChecked}
                style={{
                  background: reportLoading ? '#aaa' : '#1a1a1a', color: '#fff',
                  border: 'none', borderRadius: 4, padding: '0.5rem 1.25rem',
                  fontFamily: 'inherit', fontSize: '0.9rem',
                  cursor: reportLoading ? 'default' : 'pointer', fontWeight: 600,
                }}
              >
                {reportLoading ? 'Generating…' : 'Generate Report (PDF)'}
              </button>
            )}
          </div>

          <p style={{ margin: '0.75rem 0 0', fontSize: '0.75rem', color: '#999' }}>
            Accepted: .bin .rng .dat .raw &nbsp;·&nbsp;
            Minimum: 1,000,000 bits (125 KB) &nbsp;·&nbsp;
            Level-2 mode: ≥ 100,000,000 bits (12.5 MB)
          </p>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: 4,
            padding: '0.75rem 1rem', fontSize: '0.875rem', color: '#842029', marginBottom: '1.5rem',
          }}>
            ✕ {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{
            background: '#fff', border: '1px solid #dee2e6', borderRadius: 6,
            padding: '2rem', textAlign: 'center', color: '#555', marginBottom: '1.5rem',
          }}>
            Running analysis — this may take 30–120 seconds depending on file size…
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div style={{ background: '#fff', border: '1px solid #dee2e6', borderRadius: 6, padding: '1.5rem' }}>

            {/* Report metadata block */}
            <div style={{
              marginBottom: '1.25rem', paddingBottom: '1rem',
              borderBottom: '1px solid #eee',
            }}>
              <h3 style={{ margin: '0 0 0.6rem', fontSize: '0.95rem', fontWeight: 700 }}>
                Report Metadata
              </h3>
              <MonoValue label="Report ID"    value={result.report_id} />
              <MonoValue label="SHA-256"      value={result.input_sha256} />
              <MonoValue label="Tool"         value={result.tool_version} />
              <MonoValue label="Methodology"  value={result.methodology_version} />
              <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: '#555' }}>
                <strong>File:</strong> {result.filename} &nbsp;·&nbsp;
                <strong>Size:</strong> {(result.input_size_bits / 1_000_000).toFixed(2)}M bits ({(result.input_size_bytes / 1024).toFixed(1)} KB) &nbsp;·&nbsp;
                <strong>Generated:</strong> {new Date(result.generated_at).toLocaleString()} &nbsp;·&nbsp;
                <strong>Mode:</strong> {result.nist_result.level2
                  ? `Multi-sequence Level-2 (${result.nist_result.level2.n_sequences} sequences)`
                  : 'Single-sequence'}
              </div>
              {result.nist_result.sample_info.warnings.map((w, i) => (
                <div key={i} style={{
                  marginTop: '0.4rem', fontSize: '0.8rem', color: '#856404',
                  background: '#fff3cd', border: '1px solid #ffeeba',
                  borderRadius: 3, padding: '0.3rem 0.6rem',
                }}>
                  ⚠ {w}
                </div>
              ))}
            </div>

            {/* Label legend */}
            <div style={{
              marginBottom: '1.25rem', fontSize: '0.78rem', color: '#555',
              display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center',
            }}>
              <strong style={{ marginRight: '0.25rem' }}>Legend:</strong>
              <Badge status="PASS" />
              <Badge status="BORDERLINE" />
              <Badge status="FAIL" />
              <Badge status="INDICATIVE_ONLY" label="INDICATIVE ONLY" />
              <Badge status="INCONCLUSIVE" />
              <Badge status="NOT_RUN" label="NOT RUN" />
            </div>

            {/* Jurisdiction matrix */}
            <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem', fontWeight: 700 }}>
              Jurisdiction Scoring Matrix
            </h3>
            {result.jurisdiction_scores.map(jur => (
              <JurisdictionRow key={jur.id} jur={jur} />
            ))}

            {/* NIST breakdown */}
            <CollapsibleSection title={`NIST SP 800-22 Results (${result.nist_result.tests.length} tests)`}>
              <TableWrap>
                <thead>
                  <tr>
                    <Th>Test Name</Th>
                    <Th>P-Value</Th>
                    <Th>Status</Th>
                    <Th>Detail</Th>
                  </tr>
                </thead>
                <tbody>
                  {result.nist_result.tests.map((t, i) => (
                    <NistRow key={i} test={t} />
                  ))}
                </tbody>
              </TableWrap>
            </CollapsibleSection>

            {/* Level-2 summary */}
            {result.nist_result.level2 && (() => {
              const l2 = result.nist_result.level2!
              return (
                <CollapsibleSection title={`NIST Level-2 Analysis (${l2.n_sequences} sequences)`}>
                  <p style={{ fontSize: '0.82rem', color: '#555', margin: '0 0 0.5rem' }}>
                    Proportion check: ≥96% of sequences must pass per test.
                    Uniformity check: KS test of p-value distribution vs Uniform(0,1).
                  </p>
                  <p style={{ fontSize: '0.82rem', margin: '0 0 0.5rem' }}>
                    <strong>{l2.tests_proportion_pass}</strong> of {l2.per_test.length} tests passed proportion check.{' '}
                    <strong>{l2.tests_uniformity_pass}</strong> of {l2.per_test.length} tests passed uniformity check.
                  </p>
                  <TableWrap>
                    <thead>
                      <tr>
                        <Th>Test</Th>
                        <Th>Passing</Th>
                        <Th>Proportion</Th>
                        <Th>KS p-value</Th>
                        <Th>Uniformity</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {l2.per_test.map((t, i) => (
                        <tr key={i}>
                          <td style={{ padding: '4px 8px', fontSize: '0.78rem' }}>{t.name}</td>
                          <td style={{ padding: '4px 8px', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                            {t.n_passing}/{t.n_sequences}
                            {t.proportion_passing !== null
                              ? ` (${(t.proportion_passing * 100).toFixed(1)}%)`
                              : ''}
                          </td>
                          <td style={{ padding: '4px 8px' }}><Badge status={t.proportion_result} /></td>
                          <td style={{ padding: '4px 8px', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                            {t.ks_p_value !== null ? t.ks_p_value.toFixed(4) : '—'}
                          </td>
                          <td style={{ padding: '4px 8px' }}><Badge status={t.uniformity_result} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </TableWrap>
                </CollapsibleSection>
              )
            })()}

            {/* Supplementary tests */}
            {result.supplementary_result?.tests?.length > 0 && (
              <CollapsibleSection title={`Extended Statistical Tests (${result.supplementary_result.tests.length} tests)`}>
                <p style={{ fontSize: '0.78rem', color: '#777', fontStyle: 'italic', margin: '0 0 0.5rem' }}>
                  Supplementary tests — not part of NIST SP 800-22. Do not affect jurisdiction scores.
                </p>
                <TableWrap>
                  <thead>
                    <tr>
                      <Th>Test</Th>
                      <Th>Statistic</Th>
                      <Th>P-Value</Th>
                      <Th>Status</Th>
                      <Th>Detail</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.supplementary_result.tests.map((t, i) => (
                      <SuppRow key={i} test={t} />
                    ))}
                  </tbody>
                </TableWrap>
              </CollapsibleSection>
            )}

            {/* AUP record */}
            <CollapsibleSection title="AUP Record">
              <div style={{ fontSize: '0.8rem', lineHeight: 1.8, color: '#444' }}>
                <div><strong>Accepted:</strong> {result.aup.accepted ? 'Yes' : 'No'}</div>
                <div><strong>Accepted by:</strong> {result.aup.accepted_by}</div>
                <div><strong>Timestamp (UTC):</strong> {result.aup.acceptance_timestamp_utc}</div>
                <div><strong>AUP version:</strong> {result.aup.aup_version}</div>
                <div><strong>Reference ID:</strong> {result.aup.aup_reference_id}</div>
              </div>
            </CollapsibleSection>

          </div>
        )}

        {/* Footer */}
        <footer style={{
          marginTop: '3rem', paddingTop: '1rem', borderTop: '1px solid #dee2e6',
          fontSize: '0.72rem', color: '#999', lineHeight: 1.6,
        }}>
          This tool is <strong>NOT</strong> an accredited audit and does not constitute regulatory
          compliance evidence. It cannot be submitted to any gambling authority (MGA, UKGC,
          Spillemyndigheden, Canadian provincial regulators) in support of a licence application.
          A PASS result here does not guarantee a pass in a formal accredited audit.
        </footer>
      </div>
    </div>
  )
}
