// CheckMeIn kiosk service worker (served at /sw.js, registered by kiosk pages).
//
// Keeps kiosk pages (/station, /guests, /certifications) from getting stuck on
// the browser's error page when the server or network is briefly down. A page
// load that fails (network error or 5xx from the server or proxy) is answered
// with a "Reconnecting…" page that retries on its own and returns to the kiosk
// page once the server answers.
//
// Nothing from the server is cached, so deploys take effect immediately.
// Requests outside the kiosk pages are never touched.
//
// Kill switch: if this worker ever misbehaves, replace this file's contents with
//   self.addEventListener('install', () => self.skipWaiting());
//   self.addEventListener('activate', () => self.registration.unregister());
// and deploy. Browsers pick up the new worker on the next page load.

const KIOSK_PREFIXES = ['/station', '/guests', '/certifications'];
const SCAN_PATH = '/station/scanned';
const RETRY_INTERVAL_MS = 10000;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.mode !== 'navigate') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || !isKioskPath(url.pathname)) return;
  event.respondWith(handleNavigation(req, url));
});

function isKioskPath(path) {
  return KIOSK_PREFIXES.some((p) => path === p || path.startsWith(p + '/'));
}

async function handleNavigation(req, url) {
  try {
    const res = await fetch(req);
    // status 0 is the opaque redirect the server sends after a scan.
    if (res.status < 500) return res;
  } catch (err) {
    // Network error: server or network is down.
  }
  return offlinePage(retryTarget(req, url), url.pathname === SCAN_PATH);
}

// Where the "Reconnecting…" page goes once the server answers again. Never the
// failed URL itself when that URL performs an action (scan, check in, etc.).
function retryTarget(req, url) {
  if (url.pathname.startsWith('/guests')) return '/guests';
  if (url.pathname.startsWith('/certifications') && req.method === 'GET' &&
      url.pathname !== '/certifications/addCertification') {
    return url.pathname + url.search;
  }
  return '/station';
}

function offlinePage(target, failedScan) {
  // Safe to embed in a <script>: JSON quoting plus no literal "<".
  const targetJs = JSON.stringify(target).replace(/</g, '\\u003c');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CheckMeIn – Reconnecting</title>
<style>
  body { font-family: sans-serif; text-align: center; padding: 3em 1em; color: #222; background: #fff; }
  h1 { font-size: 2.2em; margin-bottom: 0.3em; }
  .status { font-size: 1.2em; color: #555; }
  .failed { font-size: 1.6em; color: #b00020; font-weight: bold; }
</style>
</head>
<body>
<h1>Can't reach the CheckMeIn server</h1>
${failedScan ? '<p class="failed">Your scan was not recorded. Please scan again once this page goes back to normal.</p>' : ''}
<p class="status">Retrying automatically. This page will go back to normal once the connection returns.</p>
<script>
  var target = ${targetJs};
  // A manual refresh should retry the kiosk page, not repeat a failed action.
  history.replaceState(null, '', target);
  function check() {
    fetch(target, { cache: 'no-store' })
      .then(function (res) {
        if (res.ok) location.replace(target);
        else setTimeout(check, ${RETRY_INTERVAL_MS});
      })
      .catch(function () { setTimeout(check, ${RETRY_INTERVAL_MS}); });
  }
  setTimeout(check, ${RETRY_INTERVAL_MS});
</script>
</body>
</html>`;

  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}
