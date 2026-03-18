import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API = process.env.ARES_API_URL ?? 'http://localhost:8000';

export async function POST(req: NextRequest) {
  const params = await req.json();

  try {
    const res = await fetch(`${PYTHON_API}/api/simulate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(params),
      signal:  AbortSignal.timeout(20_000),
    });
    if (!res.ok) throw new Error(`Python API returned ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: 'Python API unavailable', detail: String(err) },
      { status: 503 },
    );
  }
}
