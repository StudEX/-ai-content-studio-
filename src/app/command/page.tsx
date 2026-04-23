'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'

// ── Types ────────────────────────────────────────────────────────────────
interface Agent {
  id: string; name: string; description: string
  status: 'idle' | 'working' | 'error' | 'offline'
}

interface KanbanCard {
  id: string; title: string; agent?: string
  priority: 'High' | 'Medium' | 'Low'
  column: string; elapsed?: string; type?: string
}

interface HealthData {
  ollama: string; claude: string; higgsfield: string
  supabase: string; agents_loaded: number; time_sast: string
}

// ── API helper ───────────────────────────────────────────────────────────
const api = {
  get: async (endpoint: string) => {
    const res = await fetch(`/api/platform?endpoint=${encodeURIComponent(endpoint)}`)
    return res.json()
  },
  post: async (endpoint: string, body: Record<string, unknown> = {}) => {
    const res = await fetch(`/api/platform?endpoint=${encodeURIComponent(endpoint)}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return res.json()
  },
  patch: async (endpoint: string, body: Record<string, unknown>) => {
    const res = await fetch(`/api/platform?endpoint=${encodeURIComponent(endpoint)}&method=PATCH`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return res.json()
  },
}

// ── Agent icons by key ───────────────────────────────────────────────────
const AGENT_ICONS: Record<string, string> = {
  content: '✍️', campaign: '🚀', audience: '👥', seo: '🔍',
  social: '📡', email: '✉️', analytics: '📊', brand: '🛡️', research: '🔬',
}

// ── Priority / status colours ────────────────────────────────────────────
const priorityColor: Record<string, string> = { High: 'bg-red-500', Medium: 'bg-amber-500', Low: 'bg-green-500' }
const statusDot: Record<string, string> = { idle: 'bg-gray-500', working: 'bg-green-400 animate-pulse', error: 'bg-red-500', offline: 'bg-gray-700' }
const KANBAN_COLUMNS = ['ASSIGNED', 'BUSY', 'APPROVAL', 'DONE']

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

// ── New Task Modal ───────────────────────────────────────────────────────
function NewTaskModal({ agents, onClose, onCreated }: {
  agents: Agent[]; onClose: () => void; onCreated: (card: KanbanCard) => void
}) {
  const [title, setTitle] = useState('')
  const [agent, setAgent] = useState('')
  const [priority, setPriority] = useState('Medium')

  const submit = async () => {
    if (!title.trim()) return
    const result = await api.post('/api/tasks', { title, agent: agent || undefined, priority })
    onCreated({ id: result.id, title, agent, priority: priority as KanbanCard['priority'], column: 'ASSIGNED' })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 font-mono" onClick={onClose}>
      <div className="bg-obsidian-100 border border-gray-700 rounded-lg p-6 w-96" onClick={e => e.stopPropagation()}>
        <h3 className="text-ember font-bold mb-4">NEW TASK</h3>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Task title"
          className="w-full bg-obsidian border border-gray-700 text-white px-3 py-2 rounded mb-3 focus:border-ember focus:outline-none" />
        <select value={agent} onChange={e => setAgent(e.target.value)}
          className="w-full bg-obsidian border border-gray-700 text-white px-3 py-2 rounded mb-3 focus:border-ember focus:outline-none">
          <option value="">No agent assigned</option>
          {agents.map(a => <option key={a.id} value={a.name}>{AGENT_ICONS[a.id] || '🤖'} {a.name}</option>)}
        </select>
        <select value={priority} onChange={e => setPriority(e.target.value)}
          className="w-full bg-obsidian border border-gray-700 text-white px-3 py-2 rounded mb-4 focus:border-ember focus:outline-none">
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <div className="flex gap-2">
          <button onClick={submit} className="flex-1 bg-ember hover:bg-ember-600 text-white py-2 rounded font-bold">CREATE</button>
          <button onClick={onClose} className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded">CANCEL</button>
        </div>
      </div>
    </div>
  )
}

// ── Main Dashboard ───────────────────────────────────────────────────────
export default function CommandCentre() {
  const [authed, setAuthed] = useState(false)
  const [checking, setChecking] = useState(true)
  const [agents, setAgents] = useState<Agent[]>([])
  const [cards, setCards] = useState<KanbanCard[]>([])
  const [health, setHealth] = useState<HealthData | null>(null)
  const [backendOnline, setBackendOnline] = useState(true)
  const [dragId, setDragId] = useState<string | null>(null)
  const [clock, setClock] = useState('')
  const [noHands, setNoHands] = useState(false)
  const [showNewTask, setShowNewTask] = useState(false)
  const [commandInput, setCommandInput] = useState('')
  const [commandResult, setCommandResult] = useState<string | null>(null)
  const [commandLoading, setCommandLoading] = useState(false)

  // Check auth on mount
  useEffect(() => {
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

  // Fetch live data from backend
  const fetchData = useCallback(async () => {
    try {
      const [agentRes, taskRes, healthRes] = await Promise.all([
        api.get('/api/agents'),
        api.get('/api/tasks'),
        api.get('/api/health'),
      ])

      if (!agentRes.offline) {
        setBackendOnline(true)
        if (agentRes.agents) {
          setAgents(agentRes.agents.map((a: Record<string, string>) => ({
            id: a.id, name: a.name, description: a.description, status: a.status || 'idle',
          })))
        }
        if (taskRes.tasks) {
          setCards(taskRes.tasks.map((t: Record<string, string>) => ({
            id: t.id, title: t.title, agent: t.agent, priority: t.priority || 'Medium',
            column: t.column || 'ASSIGNED', type: t.type, elapsed: t.elapsed,
          })))
        }
        if (healthRes.status) setHealth(healthRes as HealthData)
      } else {
        setBackendOnline(false)
      }
    } catch {
      setBackendOnline(false)
    }
  }, [])

  useEffect(() => {
    if (!authed) return
    fetchData()
    const i = setInterval(fetchData, 10000) // refresh every 10s
    return () => clearInterval(i)
  }, [authed, fetchData])

  const handleAuth = () => {
    setAuthed(true)
    localStorage.setItem('naledi-auth', 'granted')
  }

  // Drag and drop — update backend
  const onDragStart = (id: string) => setDragId(id)
  const onDrop = useCallback(async (col: string) => {
    if (!dragId) return
    setCards(prev => prev.map(c => c.id === dragId ? { ...c, column: col } : c))
    await api.patch(`/api/tasks/${dragId}`, { column: col })
    setDragId(null)
  }, [dragId])

  // Command shell
  const runCommand = async () => {
    if (!commandInput.trim()) return
    setCommandLoading(true)
    setCommandResult(null)
    const res = await api.post('/api/command', { command: commandInput })
    setCommandResult(res.result?.output || res.error || JSON.stringify(res))
    setCommandLoading(false)
    setCommandInput('')
    fetchData() // refresh agents after command
  }

  if (checking) return <div className="min-h-screen bg-obsidian" />
  if (!authed) return <Gate onAuth={handleAuth} />

  const busyAgents = agents.filter(a => a.status === 'working').length
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
            {!backendOnline && <p className="text-red-500 text-xs mt-1 animate-pulse">BACKEND OFFLINE &mdash; showing cached data</p>}
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
        {/* ── COMMAND INPUT ──────────────────────────────────────────── */}
        <div className="bg-obsidian-100 border border-gray-800 rounded p-3">
          <div className="flex gap-2">
            <span className="text-ember font-bold mt-2">$</span>
            <input
              value={commandInput} onChange={e => setCommandInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && runCommand()}
              placeholder="Type a command... (e.g. 'write a blog post about biltong' or 'research competitors')"
              className="flex-1 bg-transparent text-white focus:outline-none text-sm"
              disabled={commandLoading}
            />
            <button onClick={runCommand} disabled={commandLoading}
              className="bg-ember hover:bg-ember-600 text-white px-4 py-1 rounded text-xs font-bold disabled:opacity-50">
              {commandLoading ? 'RUNNING...' : 'EXECUTE'}
            </button>
          </div>
          {commandResult && (
            <div className="mt-3 p-3 bg-obsidian border border-gray-700 rounded text-xs text-gray-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
              {commandResult}
            </div>
          )}
        </div>

        {/* ── METRICS ROW ──────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'ACTIVE TASKS', value: cards.filter(c => c.column !== 'DONE').length, color: 'text-ember' },
            { label: 'AGENTS LOADED', value: `${agents.length > 0 ? busyAgents : '?'}/${agents.length || '?'}`, color: 'text-terminal' },
            { label: 'AWAITING APPROVAL', value: approvalCount, color: 'text-signal' },
            { label: 'BACKEND', value: backendOnline ? 'ONLINE' : 'OFFLINE', color: backendOnline ? 'text-terminal' : 'text-red-500' },
          ].map(m => (
            <div key={m.label} className="bg-obsidian-100 border border-gray-800 rounded p-3">
              <div className="text-gray-500 text-xs">{m.label}</div>
              <div className={`text-xl font-bold ${m.color}`}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* ── SOCIAL METRICS (static until APIs connected) ─────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { platform: 'INSTAGRAM', reach: '—', engage: 'Connect in Settings', icon: '📸' },
            { platform: 'FACEBOOK', reach: '—', engage: 'Connect in Settings', icon: '📘' },
            { platform: 'WHATSAPP', reach: '—', engage: 'Connect in Settings', icon: '💬' },
            { platform: 'GOOGLE ADS', reach: '—', engage: 'Connect in Settings', icon: '📢' },
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

        {/* ── AGENT GRID (live from backend) ───────────────────────── */}
        <div>
          <h2 className="text-xs text-gray-500 mb-2 tracking-widest">
            AGENT SWARM &mdash; {agents.length > 0 ? `${busyAgents} ACTIVE` : 'LOADING...'}
          </h2>
          <div className="grid grid-cols-3 md:grid-cols-3 lg:grid-cols-9 gap-2">
            {(agents.length > 0 ? agents : Array.from({ length: 9 }, (_, i) => ({
              id: String(i), name: '...', description: 'Loading', status: 'offline' as const,
            }))).map(a => (
              <div key={a.id} className="bg-obsidian-100 border border-gray-800 rounded p-2 hover:border-ember/30 transition-colors">
                <div className="flex items-center gap-1.5 mb-1">
                  <div className={`w-2 h-2 rounded-full ${statusDot[a.status] || statusDot.offline}`} />
                  <span className="text-xs font-bold truncate">{AGENT_ICONS[a.id] || '🤖'} {a.name.replace('Agent', '')}</span>
                </div>
                <div className="text-[10px] text-gray-500 truncate">{a.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── KANBAN BOARD (live from backend) ─────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xs text-gray-500 tracking-widest">TASK BOARD &mdash; DRAG TO MOVE</h2>
            <button onClick={() => setShowNewTask(true)}
              className="text-xs bg-ember/20 text-ember px-3 py-1 rounded hover:bg-ember/40 font-bold">
              + NEW TASK
            </button>
          </div>
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
                        <div className={`w-1.5 h-1.5 rounded-full ${priorityColor[card.priority] || 'bg-gray-500'}`} />
                        <span className="text-xs font-bold text-white truncate">{card.title}</span>
                      </div>
                      {card.agent && <div className="text-[10px] text-gray-500">{card.agent}</div>}
                      <div className="flex items-center justify-between mt-1">
                        {card.type && <span className="text-[9px] text-gray-600 truncate">{card.type}</span>}
                        {card.elapsed && <span className="text-[10px] text-ember font-mono">{card.elapsed}</span>}
                        {col === 'APPROVAL' && (
                          <button
                            onClick={async () => {
                              setCards(prev => prev.map(c => c.id === card.id ? { ...c, column: 'DONE' } : c))
                              await api.patch(`/api/tasks/${card.id}`, { column: 'DONE' })
                            }}
                            className="text-[9px] bg-ember/20 text-ember px-1.5 rounded hover:bg-ember/40"
                          >
                            APPROVE
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  {cards.filter(c => c.column === col).length === 0 && (
                    <div className="text-[10px] text-gray-700 text-center py-4">Drop tasks here</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── HEALTH / MODEL STATUS (live) ─────────────────────────── */}
        <div className="bg-obsidian-100 border border-gray-800 rounded p-3 flex flex-wrap items-center gap-4 text-xs">
          <div><span className="text-gray-500">CLAUDE:</span> <span className={health?.claude === 'configured' ? 'text-terminal font-bold' : 'text-red-400'}>{health?.claude || '...'}</span></div>
          <div><span className="text-gray-500">OLLAMA:</span> <span className={health?.ollama === 'connected' ? 'text-terminal font-bold' : 'text-gray-400'}>{health?.ollama || '...'}</span></div>
          <div><span className="text-gray-500">HIGGSFIELD:</span> <span className="text-gray-400">{health?.higgsfield || '...'}</span></div>
          <div><span className="text-gray-500">SUPABASE:</span> <span className="text-gray-400">{health?.supabase || '...'}</span></div>
          <div><span className="text-gray-500">AGENTS:</span> <span className="text-white">{health?.agents_loaded || '...'}</span></div>
          <div><span className="text-gray-500">COST:</span> <span className="text-terminal font-bold">R0.00 (local)</span></div>
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
                { agent: 'Research', status: 'scheduled', time: '00:00', icon: '⏰' },
                { agent: 'Prompts', status: 'waiting', time: '', icon: '○' },
                { agent: 'Video', status: 'waiting', time: '', icon: '○' },
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

      {/* ── NEW TASK MODAL ─────────────────────────────────────────── */}
      {showNewTask && <NewTaskModal agents={agents} onClose={() => setShowNewTask(false)} onCreated={card => setCards(prev => [...prev, card])} />}
    </div>
  )
}
