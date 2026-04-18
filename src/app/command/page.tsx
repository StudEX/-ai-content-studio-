'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'

// ── Types ────────────────────────────────────────────────────────────────
interface Agent {
  id: string; name: string; role: string; icon: string
  status: 'idle' | 'working' | 'error' | 'offline'
  currentTask?: string; progress?: number
}

interface KanbanCard {
  id: string; title: string; agent?: string
  priority: 'High' | 'Medium' | 'Low'
  column: string; elapsed?: string; type?: string
}

interface MemoryEntry {
  id: string; task: string; date: string; duration: string
  category: string; status: string; tokens: number
}

// ── Data ─────────────────────────────────────────────────────────────────
const AGENTS: Agent[] = [
  { id: 'research', name: 'ResearchAgent', role: 'Perplexity/Gemini', icon: '🔍', status: 'working', currentTask: 'Competitor analysis', progress: 72 },
  { id: 'prompt', name: 'PromptAgent', role: 'Claude Prompts', icon: '✍️', status: 'idle' },
  { id: 'video', name: 'VideoAgent', role: 'Higgsfield Video', icon: '🎬', status: 'working', currentTask: 'Wagyu reel gen', progress: 45 },
  { id: 'caption', name: 'CaptionAgent', role: 'Copy Generation', icon: '💬', status: 'idle' },
  { id: 'distro', name: 'DistributionAgent', role: 'Social Posting', icon: '📡', status: 'idle' },
  { id: 'analytics', name: 'AnalyticsAgent', role: 'Meta/Google Ads', icon: '📊', status: 'working', currentTask: 'Daily pull', progress: 88 },
  { id: 'memory', name: 'MemoryAgent', role: 'ChromaDB/RAG', icon: '🧠', status: 'idle' },
  { id: 'trend', name: 'TrendAgent', role: 'Model Monitor', icon: '📈', status: 'idle' },
  { id: 'training', name: 'TrainingAgent', role: 'NotebookLM Sync', icon: '🎓', status: 'offline' },
]

const KANBAN_COLUMNS = ['ASSIGNED', 'BUSY', 'APPROVAL', 'DONE']

const initialCards: KanbanCard[] = [
  { id: '1', title: 'Easter campaign brief', agent: 'ResearchAgent', priority: 'High', column: 'BUSY', elapsed: '14:33', type: 'Research + Dev' },
  { id: '2', title: 'Generate 5 video prompts', agent: 'PromptAgent', priority: 'High', column: 'APPROVAL', type: 'Coding + Programing' },
  { id: '3', title: 'Wagyu hero reel', agent: 'VideoAgent', priority: 'Medium', column: 'BUSY', elapsed: '08:21', type: 'Marketing + Content' },
  { id: '4', title: 'Easter captions x5', agent: 'CaptionAgent', priority: 'Medium', column: 'DONE', type: 'Marketing + Content' },
  { id: '5', title: 'Pull Meta insights', agent: 'AnalyticsAgent', priority: 'Low', column: 'ASSIGNED', type: 'Planning' },
  { id: '6', title: 'Index vault notes', agent: 'MemoryAgent', priority: 'Low', column: 'ASSIGNED', type: 'Research + Dev' },
  { id: '7', title: 'Deploy landing page v2', agent: 'DistributionAgent', priority: 'High', column: 'ASSIGNED', type: 'Product Launch' },
  { id: '8', title: 'A/B test hook variants', agent: 'PromptAgent', priority: 'Medium', column: 'APPROVAL', type: 'Marketing + Content' },
]

const MEMORY_LOG: MemoryEntry[] = [
  { id: '1', task: 'WhatsApp bridge + gateway setup', date: '2026-04-02', duration: '45 min', category: 'setup', status: 'done', tokens: 0 },
  { id: '2', task: 'Ollama 3-tier routing system', date: '2026-04-02', duration: '15 min', category: 'feature', status: 'done', tokens: 0 },
  { id: '3', task: 'Killed OpenClaw services', date: '2026-04-02', duration: '20 min', category: 'fix', status: 'done', tokens: 0 },
  { id: '4', task: 'Connected Gmail, GitHub, Vercel', date: '2026-04-02', duration: '10 min', category: 'setup', status: 'done', tokens: 0 },
  { id: '5', task: 'Fish Audio TTS provider', date: '2026-04-02', duration: '8 min', category: 'feature', status: 'done', tokens: 0 },
  { id: '6', task: 'MiMo API key added', date: '2026-04-02', duration: '2 min', category: 'setup', status: 'done', tokens: 0 },
  { id: '7', task: 'Cyberpunk dashboard build', date: '2026-04-02', duration: 'in progress', category: 'feature', status: 'in-progress', tokens: 0 },
]

// ── Priority / Category colors ───────────────────────────────────────────
const priorityColor = { High: 'bg-red-500', Medium: 'bg-amber-500', Low: 'bg-green-500' }
const categoryColor: Record<string,string> = { setup: 'text-blue-400', fix: 'text-red-400', feature: 'text-green-400', optimization: 'text-orange-400', research: 'text-purple-400' }
const statusDot = { idle: 'bg-gray-500', working: 'bg-green-400 animate-pulse', error: 'bg-red-500', offline: 'bg-gray-700' }

// ── Gate Component ───────────────────────────────────────────────────────
function Gate({ onAuth }: { onAuth: () => void }) {
  const [pw, setPw] = useState('')
  const [err, setErr] = useState(false)

  const submit = async () => {
    const res = await fetch('/api/gate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: pw }) })
    if (res.ok) onAuth()
    else setErr(true)
  }

  return (
    <div className="min-h-screen bg-obsidian flex items-center justify-center font-mono">
      <div className="text-center">
        <div className="relative w-48 h-48 mx-auto mb-8 rounded-full overflow-hidden" style={{ boxShadow: '0 0 40px rgba(255,69,0,0.4)' }}>
          <Image src="/hero-robot.jpeg" alt="NALEDI" fill className="object-cover" />
        </div>
        <h1 className="text-3xl font-bold text-ember mb-2" style={{ textShadow: '0 0 20px rgba(255,69,0,0.5)' }}>NALEDI NEXUS</h1>
        <p className="text-gray-500 mb-8 text-sm">COMMAND CENTRE ACCESS</p>
        <input
          type="password" value={pw} onChange={e => { setPw(e.target.value); setErr(false) }}
          onKeyDown={e => e.key === 'Enter' && submit()}
          placeholder="Enter access code"
          className="bg-obsidian-100 border border-gray-700 text-white px-4 py-3 rounded text-center w-64 focus:border-ember focus:outline-none focus:ring-1 focus:ring-ember"
        />
        <br />
        <button onClick={submit} className="mt-4 bg-ember hover:bg-ember-600 text-white px-8 py-2 rounded font-bold tracking-wider">
          AUTHENTICATE
        </button>
        {err && <p className="text-red-500 mt-3 text-sm">ACCESS DENIED</p>}
      </div>
    </div>
  )
}

// ── Main Dashboard ───────────────────────────────────────────────────────
export default function CommandCentre() {
  const [authed, setAuthed] = useState(false)
  const [checking, setChecking] = useState(true)
  const [cards, setCards] = useState(initialCards)
  const [dragId, setDragId] = useState<string | null>(null)
  const [clock, setClock] = useState('')
  const [noHands, setNoHands] = useState(false)

  // Check auth cookie on mount
  useEffect(() => {
    fetch('/api/gate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: '' }) })
      .then(() => {
        // Check if cookie exists by trying a simple check
        if (document.cookie.includes('naledi-auth') || localStorage.getItem('naledi-auth')) {
          setAuthed(true)
        }
      })
      .finally(() => setChecking(false))
    // Also check localStorage fallback
    if (localStorage.getItem('naledi-auth') === 'granted') setAuthed(true)
    setChecking(false)
  }, [])

  // SAST clock
  useEffect(() => {
    const tick = () => {
      const now = new Date()
      setClock(now.toLocaleString('en-ZA', { timeZone: 'Africa/Johannesburg', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }))
    }
    tick()
    const i = setInterval(tick, 1000)
    return () => clearInterval(i)
  }, [])

  const handleAuth = () => {
    setAuthed(true)
    localStorage.setItem('naledi-auth', 'granted')
  }

  // Drag and drop
  const onDragStart = (id: string) => setDragId(id)
  const onDrop = useCallback((col: string) => {
    if (!dragId) return
    setCards(prev => prev.map(c => c.id === dragId ? { ...c, column: col } : c))
    setDragId(null)
  }, [dragId])

  if (checking) return <div className="min-h-screen bg-obsidian" />
  if (!authed) return <Gate onAuth={handleAuth} />

  const busyAgents = AGENTS.filter(a => a.status === 'working').length
  const approvalCount = cards.filter(c => c.column === 'APPROVAL').length

  return (
    <div className="min-h-screen bg-obsidian text-gray-200 font-mono overflow-x-hidden">
      {/* ── HERO HEADER ──────────────────────────────────────────────── */}
      <div className="relative h-40 overflow-hidden">
        <Image src="/hero-robot.jpeg" alt="" fill className="object-cover opacity-30" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-obsidian" />
        <div className="absolute inset-0 flex items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-bold text-ember" style={{ textShadow: '0 0 20px rgba(255,69,0,0.6)' }}>
              NALEDI NEXUS
            </h1>
            <p className="text-gray-400 text-xs mt-1">COMMAND CENTRE v1.0 &mdash; STUDEX GLOBAL MARKETS</p>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">NO-HANDS</span>
              <button onClick={() => setNoHands(!noHands)} className={`w-12 h-6 rounded-full transition-all ${noHands ? 'bg-ember' : 'bg-gray-700'} relative`}>
                <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${noHands ? 'left-6' : 'left-0.5'}`} />
              </button>
            </div>
            <div className="text-right">
              <div className="text-ember text-lg font-bold">{clock}</div>
              <div className="text-gray-500 text-xs">SAST</div>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 pb-8 space-y-4">
        {/* ── METRICS ROW ──────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'ACTIVE TASKS', value: cards.filter(c => c.column !== 'DONE').length, color: 'text-ember' },
            { label: 'AGENTS BUSY', value: `${busyAgents}/9`, color: 'text-terminal' },
            { label: 'AWAITING APPROVAL', value: approvalCount, color: 'text-signal' },
            { label: 'TOKEN BURN TODAY', value: 'R0.00', color: 'text-green-400' },
          ].map(m => (
            <div key={m.label} className="bg-obsidian-100 border border-gray-800 rounded p-3">
              <div className="text-gray-500 text-xs">{m.label}</div>
              <div className={`text-xl font-bold ${m.color}`}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* ── SOCIAL METRICS ───────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { platform: 'INSTAGRAM', reach: '2.4k', engage: '4.2%', icon: '📸' },
            { platform: 'FACEBOOK', reach: '1.8k', engage: '3.1%', icon: '📘' },
            { platform: 'WHATSAPP', reach: '847 msgs', engage: '94% read', icon: '💬' },
            { platform: 'GOOGLE ADS', reach: 'R1,240', engage: '3.8x ROAS', icon: '📢' },
          ].map(s => (
            <div key={s.platform} className="bg-obsidian-100 border border-gray-800 rounded p-3">
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                <span>{s.icon}</span>{s.platform}
              </div>
              <div className="text-sm font-bold text-white">{s.reach}</div>
              <div className="text-xs text-gray-400">{s.engage}</div>
            </div>
          ))}
        </div>

        {/* ── AGENT GRID ───────────────────────────────────────────── */}
        <div>
          <h2 className="text-xs text-gray-500 mb-2 tracking-widest">AGENT SWARM &mdash; {busyAgents} ACTIVE</h2>
          <div className="grid grid-cols-3 md:grid-cols-3 lg:grid-cols-9 gap-2">
            {AGENTS.map(a => (
              <div key={a.id} className="bg-obsidian-100 border border-gray-800 rounded p-2 hover:border-ember/30 transition-colors">
                <div className="flex items-center gap-1.5 mb-1">
                  <div className={`w-2 h-2 rounded-full ${statusDot[a.status]}`} />
                  <span className="text-xs font-bold truncate">{a.icon} {a.name.replace('Agent','')}</span>
                </div>
                <div className="text-[10px] text-gray-500 truncate">{a.role}</div>
                {a.currentTask && (
                  <>
                    <div className="text-[10px] text-gray-400 mt-1 truncate">{a.currentTask}</div>
                    <div className="w-full bg-gray-800 rounded-full h-1 mt-1">
                      <div className="bg-ember h-1 rounded-full transition-all" style={{ width: `${a.progress || 0}%` }} />
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── KANBAN BOARD ─────────────────────────────────────────── */}
        <div>
          <h2 className="text-xs text-gray-500 mb-2 tracking-widest">TASK BOARD &mdash; DRAG TO MOVE</h2>
          <div className="grid grid-cols-4 gap-2 min-h-[200px]">
            {KANBAN_COLUMNS.map(col => (
              <div
                key={col}
                onDragOver={e => e.preventDefault()}
                onDrop={() => onDrop(col)}
                className="bg-obsidian-100 border border-gray-800 rounded p-2"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-400">{col}</span>
                  <span className="text-[10px] bg-gray-800 text-gray-500 px-1.5 rounded">{cards.filter(c => c.column === col).length}</span>
                </div>
                <div className="space-y-2">
                  {cards.filter(c => c.column === col).map(card => (
                    <div
                      key={card.id}
                      draggable
                      onDragStart={() => onDragStart(card.id)}
                      className="bg-obsidian border border-gray-700 rounded p-2 cursor-grab active:cursor-grabbing hover:border-ember/40 transition-colors"
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className={`w-1.5 h-1.5 rounded-full ${priorityColor[card.priority]}`} />
                        <span className="text-xs font-bold text-white truncate">{card.title}</span>
                      </div>
                      {card.agent && <div className="text-[10px] text-gray-500">{card.agent}</div>}
                      <div className="flex items-center justify-between mt-1">
                        {card.type && <span className="text-[9px] text-gray-600 truncate">{card.type}</span>}
                        {card.elapsed && <span className="text-[10px] text-ember font-mono">{card.elapsed}</span>}
                        {col === 'APPROVAL' && (
                          <button
                            onClick={() => setCards(prev => prev.map(c => c.id === card.id ? { ...c, column: 'DONE' } : c))}
                            className="text-[9px] bg-ember/20 text-ember px-1.5 rounded hover:bg-ember/40"
                          >
                            APPROVE
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── MODEL STATUS ─────────────────────────────────────────── */}
        <div className="bg-obsidian-100 border border-gray-800 rounded p-3 flex flex-wrap items-center gap-4 text-xs">
          <div><span className="text-gray-500">MODEL:</span> <span className="text-terminal font-bold">qwen2.5:1.5b</span></div>
          <div><span className="text-gray-500">SPEED:</span> <span className="text-white">~35 t/s</span></div>
          <div><span className="text-gray-500">CONTEXT:</span> <span className="text-white">4096 / 32768</span></div>
          <div><span className="text-gray-500">RAM:</span> <span className="text-white">986 MB</span></div>
          <div><span className="text-gray-500">COST:</span> <span className="text-terminal font-bold">R0.00 (local)</span></div>
          <div><span className="text-gray-500">PROVIDER:</span> <span className="text-white">Ollama @ localhost:11434</span></div>
        </div>

        {/* ── MEMORY LOG ───────────────────────────────────────────── */}
        <div>
          <h2 className="text-xs text-gray-500 mb-2 tracking-widest">MEMORY LOG</h2>
          <div className="bg-obsidian-100 border border-gray-800 rounded overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500">
                  <th className="text-left p-2">DATE</th>
                  <th className="text-left p-2">TASK</th>
                  <th className="text-left p-2">CATEGORY</th>
                  <th className="text-left p-2">STATUS</th>
                  <th className="text-left p-2">DURATION</th>
                  <th className="text-left p-2">TOKENS</th>
                </tr>
              </thead>
              <tbody>
                {MEMORY_LOG.map(m => (
                  <tr key={m.id} className="border-b border-gray-800/50 hover:bg-obsidian-50/50">
                    <td className="p-2 text-gray-500">{m.date}</td>
                    <td className="p-2 text-white">{m.task}</td>
                    <td className={`p-2 ${categoryColor[m.category] || 'text-gray-400'}`}>{m.category}</td>
                    <td className="p-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${m.status === 'done' ? 'bg-green-900/40 text-green-400' : 'bg-amber-900/40 text-amber-400'}`}>
                        {m.status}
                      </span>
                    </td>
                    <td className="p-2 text-gray-400">{m.duration}</td>
                    <td className="p-2 text-gray-500">{m.tokens}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── TREND FEED + RALF LOOP ──────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-obsidian-100 border border-gray-800 rounded p-3">
            <h3 className="text-xs text-gray-500 mb-2 tracking-widest">TREND FEED</h3>
            <div className="space-y-1.5 text-xs">
              {[
                { tag: 'NEW', text: 'Qwen3 32B available on Ollama', color: 'text-terminal' },
                { tag: 'NEW', text: 'Higgsfield Kling 3.1 released', color: 'text-terminal' },
                { tag: 'HOT', text: 'LTX-2 video model open source', color: 'text-ember' },
                { tag: 'TIP', text: 'Mistral Small 3.1 faster tool calls', color: 'text-signal' },
              ].map((t, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className={`${t.color} font-bold text-[10px]`}>[{t.tag}]</span>
                  <span className="text-gray-300">{t.text}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-obsidian-100 border border-gray-800 rounded p-3">
            <h3 className="text-xs text-gray-500 mb-2 tracking-widest">RALF LOOP STATUS</h3>
            <div className="space-y-1.5 text-xs">
              {[
                { agent: 'Research', status: 'done', time: '14 min ago', icon: '✓' },
                { agent: 'Prompts', status: 'done', time: '8 min ago', icon: '✓' },
                { agent: 'Video', status: 'running', time: '14 min', icon: '⟳' },
                { agent: 'Caption', status: 'waiting', time: '', icon: '○' },
                { agent: 'Distribute', status: 'waiting', time: '', icon: '○' },
                { agent: 'Analytics', status: 'scheduled', time: '06:00', icon: '⏰' },
              ].map((r, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={r.status === 'done' ? 'text-terminal' : r.status === 'running' ? 'text-ember animate-spin' : 'text-gray-600'}>{r.icon}</span>
                    <span className="text-gray-300">{r.agent}</span>
                  </div>
                  <span className="text-gray-500">{r.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── FOOTER ───────────────────────────────────────────────── */}
        <div className="text-center text-[10px] text-gray-700 pt-4">
          NALEDI NEXUS v1.0 &mdash; 96% LOCAL / 4% CLOUD &mdash; POWERED BY OLLAMA + CLAUDE
        </div>
      </div>
    </div>
  )
}
