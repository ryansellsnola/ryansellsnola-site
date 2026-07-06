/**
 * Cloudflare Pages Function, tap-to-dial redirect for internal tools (FIQ sheet, etc.)
 * GET /call?n=+15551234567
 * Issues a true HTTP redirect to tel:, which browsers hand off to the OS dialer
 * at the navigation layer (no client-side JS or sandboxed iframe involved).
 */

export async function onRequestGet(context) {
  const { request } = context;
  const url = new URL(request.url);
  const number = url.searchParams.get('n');

  if (!number) {
    return new Response('No phone number provided.', { status: 400 });
  }

  const telLink = `tel:${number}`;

  return new Response(
    `<!DOCTYPE html><html><body>Calling ${number}&hellip; <a href="${telLink}">Tap here if it doesn't open automatically</a></body></html>`,
    {
      status: 302,
      headers: {
        Location: telLink,
        'Content-Type': 'text/html; charset=UTF-8',
      },
    }
  );
}
