/**
 * Cloudflare Pages Function — handles lead form submissions
 * POST /submit?type=sell  or  POST /submit?type=fsbo
 * Forwards lead to Follow Up Boss API, then returns download URL if applicable.
 */

export async function onRequestPost(context) {
  const { request, env } = context;

  const FUB_API_KEY = env.FUB_API_KEY;
  if (!FUB_API_KEY) {
    return json({ ok: false, error: 'Server misconfiguration.' }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid request.' }, 400);
  }

  const { name, phone, email, type } = body;

  if (!name || !phone || !email) {
    return json({ ok: false, error: 'Name, phone, and email are required.' }, 400);
  }

  const source = type === 'fsbo'
    ? 'FSBO Lead Magnet — ryansellsnola.com/fsbo'
    : 'Seller Checklist — ryansellsnola.com';

  const tag = type === 'fsbo' ? 'FSBO' : 'Seller Lead';

  const fubPayload = {
    source,
    type: 'Registration',
    people: [
      {
        name,
        phones: [{ value: phone, type: 'mobile' }],
        emails: [{ value: email, type: 'work' }],
        tags: [tag],
      },
    ],
  };

  const fubRes = await fetch('https://api.followupboss.com/v1/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${btoa(FUB_API_KEY + ':')}`,
    },
    body: JSON.stringify(fubPayload),
  });

  if (!fubRes.ok) {
    const err = await fubRes.text();
    console.error('FUB error:', err);
    return json({ ok: false, error: 'Could not save your info. Please try again.' }, 502);
  }

  const downloadUrl = type === 'fsbo'
    ? '/assets/fsbo-toolkit.pdf'
    : '/assets/seller-checklist.pdf';

  return json({ ok: true, downloadUrl });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
