import { useState, useRef, useEffect, KeyboardEvent } from 'react'

interface LogEntry {
  type: 'input' | 'output' | 'error' | 'system'
  text: string
  agent?: string
  time: string
}

export default function CommandShell() {
  const [input, setInput] = useState('')
  const [log, setLog] = useState<LogEntry[]>([
    { type: 'system', text: 'NALEDI INTELLIGENCE PLATFORM v1.0 — Studex Meat', time: now() },
    { type: 'system', text: 'Rulofo + GSD + RALF-GIUM online. 9 agents standing by.', time: now() },
    { type: 'system', text: 'Type a command or describe a task. All times SAST. All costs ZAR.', time: now() },
  ])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [log])
  useEffect(() => { inputRef.current?.focus() }, [])

  async function handleSubmit() {
    const cmd = input.trim()
    if (!cmd) return
    setInput('')
    setLog(prev => [...prev, { type: 'input', text: cmd, time: now() }])
    setLoading(true)
    try {
      const resp = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd }),
      })
      const data = await resp.json()
      if (data.error) {
        setLog(prev => [...prev, { type: 'error', text: data.error, time: now() }])
      } else {
        setLog(prev => [...prev, {
          type: 'output',
          text: data.result?.output || JSON.stringify(data.result, null, 2),
          agent: data.agent,
          time: data.time_sast || now(),
        }])
      }
    } catch (err: any) {
      setLog(prev => [...prev, { type: 'error', text: `Connection error: ${err.message}`, time: now() }])
    }
    setLoading(false)
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className="flex flex-col h-full bg-obsidian">
      {/* Terminal header */}
      <div className="flex items-center gap-2 px-4 py-2 bg-obsidian-50 border-b border-gray-800">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500/80" />
          <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <span className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <span className="text-xs text-gray-500 ml-2">naledi — command shell</span>
        {loading && <span className="ml-auto text-xs text-cyan animate-pulse">processing...</span>}
      </div>

      {/* Log output */}
      <div className="flex-1 overflow-auto p-4 space-y-1 font-mono text-sm">
        {log.map((entry, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-gray-600 text-xs shrink-0 w-20">{entry.time.split('T').pop()?.slice(0, 8) || ''}</span>
            {entry.type === 'input' && (
              <span><span className="text-cyan glow-cyan">▸</span> <span className="text-gray-200">{entry.text}</span></span>
            )}
            {entry.type === 'output' && (
              <span>
                {entry.agent && <span className="text-cyan/70">[{entry.agent}]</span>}{' '}
                <span className="text-gray-300 whitespace-pre-wrap">{entry.text}</span>
              </span>
            )}
            {entry.type === 'error' && (
              <span className="text-red-400">✗ {entry.text}</span>
            )}
            {entry.type === 'system' && (
              <span className="text-gray-500 italic">{entry.text}</span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-4 py-3 bg-obsidian-50 border-t border-gray-800">
        <span className="text-cyan glow-cyan text-sm">naledi▸</span>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter command..."
          className="flex-1 bg-transparent outline-none text-sm text-gray-200 placeholder-gray-600 caret-cyan"
          disabled={loading}
        />
      </div>
    </div>
  )
}

function now(): string {
  return new Date().toLocaleString('en-ZA', { timeZone: 'Africa/Johannesburg', hour12: false })
}
