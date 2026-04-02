import { useState, useEffect, useRef } from 'react'
import { Clock, Zap, AlertCircle, CheckCircle } from 'lucide-react'

interface Agent {
  id: string
  name: string
  status: string
  description: string
}

interface TaskCard {
  id: string
  agent: string
  task: string
  status: 'queued' | 'running' | 'done' | 'error'
  startedAt?: number
  elapsed?: number
}

const COLUMNS = [
  { key: 'queued', label: 'QUEUED', color: 'text-gray-400', icon: Clock },
  { key: 'running', label: 'RUNNING', color: 'text-cyan', icon: Zap },
  { key: 'done', label: 'DONE', color: 'text-green-400', icon: CheckCircle },
  { key: 'error', label: 'ERROR', color: 'text-red-400', icon: AlertCircle },
] as const

export default function AgentBoard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<TaskCard[]>([])
  const [taskInput, setTaskInput] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('')
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    fetch('/api/agents')
      .then(r => r.json())
      .then(d => { setAgents(d.agents || []); if (d.agents?.[0]) setSelectedAgent(d.agents[0].id) })
      .catch(() => {})

    // Timer for live elapsed
    timerRef.current = setInterval(() => {
      setTasks(prev => prev.map(t =>
        t.status === 'running' && t.startedAt
          ? { ...t, elapsed: Math.floor((Date.now() - t.startedAt) / 1000) }
          : t
      ))
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  async function submitTask() {
    if (!taskInput.trim() || !selectedAgent) return
    const id = crypto.randomUUID().slice(0, 8)
    const card: TaskCard = { id, agent: selectedAgent, task: taskInput, status: 'queued' }
    setTasks(prev => [...prev, card])
    setTaskInput('')

    // Move to running
    setTasks(prev => prev.map(t => t.id === id ? { ...t, status: 'running', startedAt: Date.now() } : t))

    try {
      const resp = await fetch('/api/agents/task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent: selectedAgent, task: taskInput }),
      })
      const data = await resp.json()
      setTasks(prev => prev.map(t => t.id === id ? { ...t, status: data.result?.error ? 'error' : 'done' } : t))
    } catch {
      setTasks(prev => prev.map(t => t.id === id ? { ...t, status: 'error' } : t))
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h2 className="text-lg font-semibold text-cyan glow-cyan">Agent Board</h2>
          <p className="text-xs text-gray-500">{agents.length} agents loaded — 4-column Kanban</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedAgent}
            onChange={e => setSelectedAgent(e.target.value)}
            className="bg-obsidian-50 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300"
          >
            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          <input
            value={taskInput}
            onChange={e => setTaskInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submitTask()}
            placeholder="Assign task..."
            className="bg-obsidian-50 border border-gray-700 rounded px-3 py-1 text-sm text-gray-300 w-64 placeholder-gray-600"
          />
          <button onClick={submitTask} className="bg-cyan/20 text-cyan px-3 py-1 rounded text-sm hover:bg-cyan/30 transition">
            Send
          </button>
        </div>
      </div>

      {/* Kanban columns */}
      <div className="flex-1 grid grid-cols-4 gap-4 p-6 overflow-auto">
        {COLUMNS.map(col => {
          const colTasks = tasks.filter(t => t.status === col.key)
          const Icon = col.icon
          return (
            <div key={col.key} className="flex flex-col">
              <div className={`flex items-center gap-2 mb-3 ${col.color}`}>
                <Icon size={14} />
                <span className="text-xs font-semibold uppercase tracking-wider">{col.label}</span>
                <span className="ml-auto text-xs text-gray-600">{colTasks.length}</span>
              </div>
              <div className="space-y-2 flex-1">
                {colTasks.map(task => {
                  const agent = agents.find(a => a.id === task.agent)
                  return (
                    <div key={task.id} className="bg-obsidian-50 border border-gray-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-cyan uppercase">{agent?.name || task.agent}</span>
                        {task.status === 'running' && task.elapsed !== undefined && (
                          <span className="text-[10px] text-cyan animate-pulse">{task.elapsed}s</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-300 line-clamp-2">{task.task}</p>
                    </div>
                  )
                })}
                {colTasks.length === 0 && (
                  <div className="border border-dashed border-gray-800 rounded-lg p-4 text-center text-xs text-gray-700">
                    No tasks
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Agent status bar */}
      <div className="flex gap-4 px-6 py-3 border-t border-gray-800 overflow-x-auto">
        {agents.map(a => (
          <div key={a.id} className="flex items-center gap-2 text-xs shrink-0">
            <span className={`w-2 h-2 rounded-full ${a.status === 'idle' ? 'bg-green-500' : a.status === 'working' ? 'bg-cyan animate-pulse' : 'bg-red-500'}`} />
            <span className="text-gray-400">{a.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
