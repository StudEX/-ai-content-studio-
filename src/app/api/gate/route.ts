import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const { password } = await req.json()
  const correct = process.env.NALEDI_PASSWORD || '12345'

  if (password === correct) {
    const res = NextResponse.json({ ok: true })
    res.cookies.set('naledi-auth', 'granted', {
      httpOnly: true,
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
      sameSite: 'lax',
    })
    return res
  }

  return NextResponse.json({ ok: false }, { status: 401 })
}
