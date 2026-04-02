import { useState, useEffect } from 'react'
import { Box, Download, Film, Cpu } from 'lucide-react'

interface OllamaModel {
  name: string
  size: number
  modified_at: string
  digest: string
}

interface VideoModel {
  id: string
  name: string
  endpoint: string
}

export default function ModelBrowser() {
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([])
  const [videoModels, setVideoModels] = useState<VideoModel[]>([])
  const [ollamaOnline, setOllamaOnline] = useState(false)
  const [pullName, setPullName] = useState('')
  const [pulling, setPulling] = useState(false)
  const [tab, setTab] = useState<'ollama' | 'video'>('ollama')

  useEffect(() => {
    fetch('/api/models/ollama').then(r => r.json()).then(d => { setOllamaModels(d.models || []); setOllamaOnline(true) }).catch(() => {})
    fetch('/api/models/video').then(r => r.json()).then(d => setVideoModels(d.models || [])).catch(() => {})
  }, [])

  async function pullModel() {
    if (!pullName.trim()) return
    setPulling(true)
    try {
      await fetch(`/api/models/ollama/pull?name=${encodeURIComponent(pullName)}`, { method: 'POST' })
      const resp = await fetch('/api/models/ollama')
      const d = await resp.json()
      setOllamaModels(d.models || [])
    } catch {}
    setPulling(false)
    setPullName('')
  }

  function formatSize(bytes: number): string {
    if (bytes === 0) return '—'
    const gb = bytes / (1024 ** 3)
    return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 ** 2)).toFixed(0)} MB`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h2 className="text-lg font-semibold text-cyan glow-cyan">Model Browser</h2>
          <p className="text-xs text-gray-500">
            Ollama {ollamaOnline ? <span className="text-green-400">online</span> : <span className="text-red-400">offline</span>}
            {' · '}{ollamaModels.length} local models · {videoModels.length} video models
          </p>
        </div>
        <div className="flex gap-1">
          <button onClick={() => setTab('ollama')} className={`px-3 py-1 rounded text-sm transition ${tab === 'ollama' ? 'bg-cyan/20 text-cyan' : 'text-gray-500 hover:text-gray-300'}`}>
            <Cpu size={14} className="inline mr-1" />Ollama
          </button>
          <button onClick={() => setTab('video')} className={`px-3 py-1 rounded text-sm transition ${tab === 'video' ? 'bg-cyan/20 text-cyan' : 'text-gray-500 hover:text-gray-300'}`}>
            <Film size={14} className="inline mr-1" />fal.ai Video
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {tab === 'ollama' && (
          <>
            {/* Pull model */}
            <div className="flex gap-2 mb-6">
              <input
                value={pullName}
                onChange={e => setPullName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && pullModel()}
                placeholder="Pull model (e.g. llama3.1:8b)"
                className="bg-obsidian-50 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 flex-1 placeholder-gray-600"
              />
              <button onClick={pullModel} disabled={pulling} className="bg-cyan/20 text-cyan px-4 py-2 rounded text-sm hover:bg-cyan/30 transition disabled:opacity-50">
                <Download size={14} className="inline mr-1" />{pulling ? 'Pulling...' : 'Pull'}
              </button>
            </div>

            {/* Model list */}
            <div className="space-y-2">
              {ollamaModels.length === 0 ? (
                <div className="text-center py-12 text-gray-600">
                  {ollamaOnline ? 'No models installed. Pull one above.' : 'Ollama is offline. Run: ollama serve'}
                </div>
              ) : ollamaModels.map(m => (
                <div key={m.name} className="flex items-center justify-between bg-obsidian-50 border border-gray-800 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-3">
                    <Box size={16} className="text-cyan" />
                    <div>
                      <p className="text-sm text-gray-200 font-medium">{m.name}</p>
                      <p className="text-[10px] text-gray-600">{m.digest}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-400">{formatSize(m.size)}</p>
                    <p className="text-[10px] text-gray-600">{m.modified_at ? new Date(m.modified_at).toLocaleDateString('en-ZA') : ''}</p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === 'video' && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 mb-4">Video generation via fal.ai — Kling 3.0, Wan 2.5, LTX-Video</p>
            {videoModels.map(m => (
              <div key={m.id} className="flex items-center justify-between bg-obsidian-50 border border-gray-800 rounded-lg px-4 py-3">
                <div className="flex items-center gap-3">
                  <Film size={16} className="text-cyan" />
                  <div>
                    <p className="text-sm text-gray-200 font-medium">{m.name}</p>
                    <p className="text-[10px] text-gray-600 font-mono">{m.endpoint}</p>
                  </div>
                </div>
                <span className="text-xs text-cyan bg-cyan/10 px-2 py-1 rounded">fal.ai</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
