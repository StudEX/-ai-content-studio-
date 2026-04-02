import { useState, useEffect } from 'react'
import { Calculator, TrendingUp } from 'lucide-react'

interface PricingEntry {
  input_per_1m_zar: number
  output_per_1m_zar: number
  local: boolean
}

interface CalcResult {
  model: string
  tokens_per_day: number
  days: number
  daily_cost_zar: number
  weekly_cost_zar: number
  monthly_cost_zar: number
  total_cost_zar: number
  local: boolean
}

export default function TokenCalculator() {
  const [pricing, setPricing] = useState<Record<string, PricingEntry>>({})
  const [usdToZar, setUsdToZar] = useState(18.5)
  const [selectedModel, setSelectedModel] = useState('')
  const [tokensPerDay, setTokensPerDay] = useState(100000)
  const [days, setDays] = useState(30)
  const [result, setResult] = useState<CalcResult | null>(null)

  useEffect(() => {
    fetch('/api/tokens/pricing')
      .then(r => r.json())
      .then(d => {
        setPricing(d.pricing || {})
        setUsdToZar(d.usd_to_zar || 18.5)
        const models = Object.keys(d.pricing || {})
        if (models.length && !selectedModel) setSelectedModel(models[0])
      })
      .catch(() => {})
  }, [])

  async function calculate() {
    if (!selectedModel) return
    try {
      const resp = await fetch('/api/tokens/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel, tokens_per_day: tokensPerDay, days }),
      })
      setResult(await resp.json())
    } catch {}
  }

  const models = Object.keys(pricing)

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-gray-800">
        <h2 className="text-lg font-semibold text-cyan glow-cyan">Token Calculator</h2>
        <p className="text-xs text-gray-500">All costs in ZAR · USD/ZAR: R{usdToZar.toFixed(2)}</p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-2 gap-8 max-w-5xl">
          {/* Calculator */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Calculate Cost</h3>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Model</label>
              <select
                value={selectedModel}
                onChange={e => setSelectedModel(e.target.value)}
                className="w-full bg-obsidian-50 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300"
              >
                {models.map(m => (
                  <option key={m} value={m}>{m} {pricing[m]?.local ? '(local)' : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Tokens per day</label>
              <input
                type="number"
                value={tokensPerDay}
                onChange={e => setTokensPerDay(Number(e.target.value))}
                className="w-full bg-obsidian-50 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Duration (days)</label>
              <input
                type="number"
                value={days}
                onChange={e => setDays(Number(e.target.value))}
                className="w-full bg-obsidian-50 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300"
              />
            </div>
            <button onClick={calculate} className="w-full bg-cyan/20 text-cyan py-2 rounded text-sm font-medium hover:bg-cyan/30 transition">
              <Calculator size={14} className="inline mr-2" />Calculate ZAR Cost
            </button>

            {result && (
              <div className="bg-obsidian-50 border border-cyan/30 rounded-lg p-4 space-y-2 mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={14} className="text-cyan" />
                  <span className="text-sm text-cyan font-semibold">{result.model}</span>
                  {result.local && <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded">FREE (local)</span>}
                </div>
                <Row label="Daily" value={result.daily_cost_zar} />
                <Row label="Weekly" value={result.weekly_cost_zar} />
                <Row label="Monthly" value={result.monthly_cost_zar} />
                <div className="border-t border-gray-700 pt-2 mt-2">
                  <Row label={`Total (${result.days} days)`} value={result.total_cost_zar} bold />
                </div>
              </div>
            )}
          </div>

          {/* Pricing table */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Pricing Table (ZAR per 1M tokens)</h3>
            <div className="space-y-1">
              <div className="grid grid-cols-4 gap-2 text-[10px] text-gray-500 uppercase px-3 py-1">
                <span>Model</span><span className="text-right">Input</span><span className="text-right">Output</span><span className="text-right">Type</span>
              </div>
              {models.map(m => {
                const p = pricing[m]
                return (
                  <div key={m} className="grid grid-cols-4 gap-2 bg-obsidian-50 rounded px-3 py-2 text-sm">
                    <span className="text-gray-300 truncate">{m}</span>
                    <span className="text-right text-gray-400">{p.local ? 'Free' : `R${p.input_per_1m_zar.toFixed(2)}`}</span>
                    <span className="text-right text-gray-400">{p.local ? 'Free' : `R${p.output_per_1m_zar.toFixed(2)}`}</span>
                    <span className={`text-right text-xs ${p.local ? 'text-green-400' : 'text-cyan'}`}>{p.local ? 'Local' : 'Cloud'}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, bold }: { label: string; value: number; bold?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className={`text-sm ${bold ? 'text-gray-200 font-semibold' : 'text-gray-400'}`}>{label}</span>
      <span className={`text-sm ${bold ? 'text-cyan glow-cyan font-bold' : 'text-gray-300'}`}>
        R{value.toFixed(2)}
      </span>
    </div>
  )
}
