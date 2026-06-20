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

  const { name, phone, email, type, property } = body;

  if (!name || !phone) {
    return json({ ok: false, error: 'Name and phone are required.' }, 400);
  }
  if (type !== 'showing' && !email) {
    return json({ ok: false, error: 'Name, phone, and email are required.' }, 400);
  }

  let source, tag;
  if (type === 'fsbo') {
    source = 'FSBO Lead Magnet — ryansellsnola.com/fsbo';
    tag = 'FSBO';
  } else if (type === 'showing') {
    source = 'Showing Request — ryansellsnola.com';
    tag = 'Showing Request';
  } else {
    source = 'Seller Checklist — ryansellsnola.com';
    tag = 'Seller Lead';
  }

  const person = {
    name,
    phones: [{ value: phone }],
    tags: tag,
  };
  if (email) person.emails = [{ value: email }];

  const fubPayload = { source, type: 'Registration', person };
  if (type === 'showing' && property) {
    fubPayload.property = { street: property };
  }

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

  let downloadUrl = null;
  if (type === 'fsbo') downloadUrl = '/assets/fsbo-toolkit.pdf';
  else if (type !== 'showing') downloadUrl = '/assets/seller-checklist.pdf';

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
