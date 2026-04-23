import { NextRequest, NextResponse } from 'next/server'

const API = process.env.NALEDI_API_URL || 'http://localhost:8000'

/** Proxy GET requests to FastAPI backend */
export async function GET(req: NextRequest) {
  const endpoint = req.nextUrl.searchParams.get('endpoint')
  if (!endpoint) return NextResponse.json({ error: 'Missing endpoint param' }, { status: 400 })

  try {
    const res = await fetch(`${API}${endpoint}`, { cache: 'no-store' })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Backend unreachable'
    return NextResponse.json({ error: msg, offline: true }, { status: 502 })
  }
}

/** Proxy POST/PATCH/DELETE requests to FastAPI backend */
export async function POST(req: NextRequest) {
  const endpoint = req.nextUrl.searchParams.get('endpoint')
  if (!endpoint) return NextResponse.json({ error: 'Missing endpoint param' }, { status: 400 })

  const method = req.nextUrl.searchParams.get('method') || 'POST'
  try {
    const body = await req.json().catch(() => ({}))
    const res = await fetch(`${API}${endpoint}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Backend unreachable'
    return NextResponse.json({ error: msg, offline: true }, { status: 502 })
  }
}
