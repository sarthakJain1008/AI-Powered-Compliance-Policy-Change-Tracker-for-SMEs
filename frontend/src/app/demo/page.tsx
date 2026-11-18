'use client'

/**
 * Compliance database demo: overview, time travel (temporal "as of" query), review queue, ingested documents, calendar.
 * Talks to /api/v1/demo/* (FastAPI) which reads the temporal compliance database.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'

type Row = Record<string, any>
const TABS = ['Overview', 'Time Travel', 'Review Queue', 'Documents', 'Calendar'] as const
type Tab = (typeof TABS)[number]

const fmt = (d?: string | null) => (d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—')

function describeRule(r: Row | null): string {
  if (!r) return '—'
  switch (r.type) {
    case 'day_of_next_month': return `${r.day}th of next month`
    case 'fixed_date': return `${r.day}/${r.month} every year`
    case 'fixed_dates': return (r.dates as number[][]).map(([m, d]) => `${d}/${m}`).join(', ')
    case 'after_event': return `${r.days} days after ${String(r.event).replace('_', ' ')}`
    case 'offset_days': return `${r.days} days after effective date`
    default: return r.text ?? JSON.stringify(r)
  }
}

export default function DemoPage() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const [tab, setTab] = useState<Tab>('Overview')

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace('/login')
  }, [isLoading, isAuthenticated, router])

  if (isLoading || !isAuthenticated) return <div className="p-10 text-gray-500">Loading…</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">AI-Powered Compliance &amp; Policy Change Tracker</h1>
            <p className="text-xs text-gray-500">Versioned, temporal regulatory database for SMEs</p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-600">{user?.full_name || user?.email}</span>
            <button onClick={() => logout()} className="px-3 py-1.5 rounded border text-gray-700 hover:bg-gray-100">Log out</button>
          </div>
        </div>
        <nav className="max-w-6xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap ${tab === t ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-800'}`}>
              {t}
            </button>
          ))}
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        {tab === 'Overview' && <Overview />}
        {tab === 'Time Travel' && <TimeTravel />}
        {tab === 'Review Queue' && <ReviewQueue />}
        {tab === 'Documents' && <Documents />}
        {tab === 'Calendar' && <Calendar />}
      </main>
    </div>
  )
}

function useGet<T>(url: string, params?: Row, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(() => {
    setLoading(true)
    api.get(url, { params }).then((r) => { setData(r.data); setErr(null) })
      .catch((e) => setErr(e?.response?.data?.detail ?? e.message)).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, JSON.stringify(params), ...deps])
  useEffect(load, [load])
  return { data, err, loading, reload: load }
}

const Err = ({ msg }: { msg: string }) => <div className="rounded border border-red-200 bg-red-50 text-red-700 p-3 text-sm">{msg}</div>

function Overview() {
  const { data, err } = useGet<Row>('/demo/overview')
  if (err) return <Err msg={err} />
  if (!data) return <p className="text-gray-500">Loading…</p>
  const cards: [string, number, string][] = [
    ['Regulations', data.regulations, 'Acts, Directions, Codes tracked'],
    ['Act sections', data.sections, 'Statute text, versioned'],
    ['Obligations', data.obligations, 'Derived compliance duties'],
    ['Documents fetched', data.documents_parsed, `of ${data.documents} RBI documents (${data.documents_failed} failed)`],
    ['Awaiting review', data.review_queue, 'Low-confidence or unverified changes'],
    ['Calendar rules', data.calendar_rules, 'Statutory filing deadlines'],
  ]
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {cards.map(([t, v, s]) => (
          <div key={t} className="bg-white rounded-lg border p-4">
            <div className="text-3xl font-bold text-blue-700">{Number(v).toLocaleString('en-IN')}</div>
            <div className="font-medium text-gray-900">{t}</div>
            <div className="text-xs text-gray-500">{s}</div>
          </div>
        ))}
      </div>
      <div className="bg-white rounded-lg border p-5">
        <h2 className="font-semibold mb-3">Processing pipeline</h2>
        <ol className="flex flex-wrap items-center gap-2 text-sm">
          {['Monitor sources', 'Fetch & store raw', 'Parse & chunk', 'AI extraction', 'Resolve & version', 'Human review', 'Impact & tasks'].map((s, i, a) => (
            <li key={s} className="flex items-center gap-2">
              <span className={`px-3 py-1.5 rounded-full border ${i < 3 ? 'bg-green-50 border-green-300 text-green-800' : i < 6 ? 'bg-blue-50 border-blue-300 text-blue-800' : 'bg-gray-50 text-gray-500'}`}>{s}</span>
              {i < a.length - 1 && <span className="text-gray-400">→</span>}
            </li>
          ))}
        </ol>
        <p className="text-xs text-gray-500 mt-3">Green: running on live RBI data. Blue: built and tested (AI step needs an API key). Grey: next phase.</p>
      </div>
    </div>
  )
}

function TimeTravel() {
  const [on, setOn] = useState(new Date().toISOString().slice(0, 10))
  const [q, setQ] = useState('')
  const { data, err, loading } = useGet<Row>('/demo/regulations', { on, q })
  const [sel, setSel] = useState<Row | null>(null)
  const [tl, setTl] = useState<Row[]>([])
  const [secs, setSecs] = useState<Row[]>([])
  useEffect(() => {
    if (!sel) return
    api.get(`/demo/regulations/${sel.regulation_id}/timeline`).then((r) => setTl(r.data))
    api.get(`/demo/regulations/${sel.regulation_id}/sections`, { params: { limit: 5 } }).then((r) => setSecs(r.data))
  }, [sel])
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border p-4 flex flex-wrap items-end gap-3">
        <label className="text-sm">As of date<input type="date" value={on} onChange={(e) => setOn(e.target.value)} className="block border rounded px-2 py-1.5 mt-1" /></label>
        <label className="text-sm">Search<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. tax, wages, data" className="block border rounded px-2 py-1.5 mt-1" /></label>
        <div className="flex gap-2 text-sm">
          {[['31 Mar 2026', '2026-03-31'], ['2 Apr 2026', '2026-04-02'], ['Today', new Date().toISOString().slice(0, 10)]].map(([l, d]) => (
            <button key={l} onClick={() => setOn(d)} className="px-3 py-1.5 rounded border hover:bg-gray-100">{l}</button>
          ))}
        </div>
        <p className="text-xs text-gray-500 ml-auto max-w-sm">Answers “which regulations applied on date D?” using valid-time version ranges.</p>
      </div>
      {err && <Err msg={err} />}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border">
          <div className="px-4 py-2 border-b font-semibold text-sm">In force on {fmt(on)} {data && <span className="text-gray-500 font-normal">({data.count})</span>} {loading && '…'}</div>
          <ul className="divide-y max-h-[32rem] overflow-auto">
            {data?.in_force.map((r: Row) => (
              <li key={r.version_id} onClick={() => setSel(r)} className={`px-4 py-2 cursor-pointer hover:bg-blue-50 ${sel?.regulation_id === r.regulation_id ? 'bg-blue-50' : ''}`}>
                <div className="text-sm font-medium text-gray-900">{r.title}</div>
                <div className="text-xs text-gray-500">{r.jurisdiction} · v{r.version_number} · from {fmt(r.effective_from)}{r.effective_to ? ` to ${fmt(r.effective_to)}` : ''} · {r.sections} sections · {r.obligations} obligations</div>
              </li>
            ))}
            {data && data.in_force.length === 0 && <li className="px-4 py-6 text-sm text-gray-500">Nothing in force for this date and search.</li>}
          </ul>
          {data && data.repealed.length > 0 && (
            <div className="border-t bg-red-50 px-4 py-2">
              <div className="text-xs font-semibold text-red-800 mb-1">Repealed by this date</div>
              {data.repealed.map((r: Row) => <div key={r.regulation_id} className="text-xs text-red-700">{r.title} — repealed {fmt(r.repealed_on)}</div>)}
            </div>
          )}
        </div>
        <div className="bg-white rounded-lg border">
          <div className="px-4 py-2 border-b font-semibold text-sm">{sel ? sel.title : 'Select a regulation'}</div>
          {sel && (
            <div className="p-4 space-y-4">
              <div>
                <div className="text-xs font-semibold text-gray-600 mb-1">Version history</div>
                <ol className="space-y-1">
                  {tl.map((v) => (
                    <li key={v.version_id} className="text-sm flex flex-wrap gap-2 items-center">
                      <span className="font-medium">{v.version_number}</span><span className="text-gray-500">{fmt(v.effective_from)} → {v.effective_to ? fmt(v.effective_to) : 'current'}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${v.review_status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>{v.change_type} · {v.review_status}</span>
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <div className="text-xs font-semibold text-gray-600 mb-1">Statute text (first sections)</div>
                {secs.length === 0 && <p className="text-xs text-gray-500">No section text loaded for this regulation.</p>}
                {secs.map((s) => <p key={s.section_no} className="text-xs text-gray-700 mb-2 whitespace-pre-line"><b>§{s.section_no}</b> {s.body}</p>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ReviewQueue() {
  const { data, err, reload } = useGet<Row[]>('/demo/review-queue')
  const [busy, setBusy] = useState<number | null>(null)
  const act = async (id: number, d: 'approve' | 'reject') => { setBusy(id); try { await api.post(`/demo/review/${id}/${d}`) } finally { setBusy(null); reload() } }
  const reset = async () => { await api.post('/demo/reset-transitions'); reload() }
  return (
    <div className="space-y-4">
      <div className="rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 flex flex-wrap items-center gap-3">
        <span className="flex-1 min-w-[16rem]">These are AI/seeded changes <b>not yet verified</b>. Nothing here affects what applies to a company until a reviewer approves it. Approving a change closes the previous version the day before. Then open <b>Time Travel</b> and compare 31 Mar vs 2 Apr 2026.</span>
        <button onClick={reset} className="px-3 py-1.5 rounded border border-amber-400 bg-white hover:bg-amber-100">Reset demo</button>
      </div>
      {err && <Err msg={err} />}
      <div className="bg-white rounded-lg border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-600"><tr><th className="p-3">Regulation</th><th>Change</th><th>Effective</th><th>Note</th><th className="p-3 text-right">Decision</th></tr></thead>
          <tbody className="divide-y">
            {data?.map((r) => (
              <tr key={r.version_id}>
                <td className="p-3 font-medium">{r.regulation_title}</td>
                <td><span className="px-2 py-0.5 rounded-full text-xs bg-gray-100">{r.change_type}</span></td>
                <td>{fmt(r.effective_from)}</td>
                <td className="text-xs text-gray-600 max-w-xs">{r.summary_text}</td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button disabled={busy === r.version_id} onClick={() => act(r.version_id, 'approve')} className="px-3 py-1 rounded bg-green-600 text-white text-xs mr-2 disabled:opacity-50">Approve</button>
                  <button disabled={busy === r.version_id} onClick={() => act(r.version_id, 'reject')} className="px-3 py-1 rounded border text-xs disabled:opacity-50">Reject</button>
                </td>
              </tr>
            ))}
            {data && data.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-gray-500">Queue is empty. Use “Reset demo” to repeat the walkthrough.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Documents() {
  const [q, setQ] = useState('')
  const { data, err } = useGet<Row[]>('/demo/documents', { q, limit: 30 })
  return (
    <div className="space-y-4">
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search fetched RBI documents (title or full text)…" className="w-full border rounded px-3 py-2 bg-white" />
      {err && <Err msg={err} />}
      <div className="grid gap-3">
        {data?.map((d) => (
          <div key={d.document_id} className="bg-white rounded-lg border p-4">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="font-medium text-gray-900">{d.title}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">{d.stage}</span>
              <span className="text-xs text-gray-500">{d.reference_no} · {fmt(d.published_date)} · {Number(d.chars).toLocaleString('en-IN')} characters</span>
            </div>
            <p className="text-xs text-gray-600 whitespace-pre-line line-clamp-4">{d.excerpt}</p>
            <a href={d.url} target="_blank" rel="noreferrer" className="text-xs text-blue-700 hover:underline">Source on rbi.org.in</a>
          </div>
        ))}
      </div>
    </div>
  )
}

function Calendar() {
  const { data, err } = useGet<Row[]>('/demo/calendar')
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600">Statutory filing deadlines stored as data (rules with validity), not hardcoded dates.</p>
      {err && <Err msg={err} />}
      <div className="bg-white rounded-lg border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-600"><tr><th className="p-3">Filing</th><th>Authority</th><th>Form</th><th>Frequency</th><th>Deadline rule</th></tr></thead>
          <tbody className="divide-y">
            {data?.map((r) => (
              <tr key={r.filing}><td className="p-3 font-medium">{r.filing}</td><td>{r.authority}</td><td>{r.form}</td><td className="capitalize">{r.frequency}</td><td>{describeRule(r.deadline_rule)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
