// Page-duration check for a Lemo clip workspace.
//   node page_check.mjs <clip_dir> <expected_duration>
//
// Opens the clip page through the vendored engine (openDemo mounts a clip that
// lives outside the library under /@film/ and waits for window.READY), draws at
// t = 0 and t = window.DUR to prove window.render(t) works, and confirms the
// page's window.DUR agrees with the duration recorded in clip.json.
//
// Prints {"ok":true,"dur":6} on success. Exits non-zero (printing a JSON error
// object when it got far enough to form one) on any failure.
import { openDemo, closeServer, requireDemo } from '../library/core/render/page.mjs';

const args = process.argv.slice(2);
const dir = args[0];
const expected = Number(args[1]);

function fail(message, { json = false } = {}) {
  if (json) console.error(JSON.stringify({ ok: false, error: message }));
  else console.error('page_check: ' + message);
  process.exit(1);
}

requireDemo(dir);
if (!Number.isFinite(expected) || expected <= 0) {
  console.error('usage: node page_check.mjs <clip_dir> <expected_duration>');
  process.exit(2);
}

const { browser, page } = await openDemo(dir);
let dur = null;
let renderError = null;
try {
  const report = await page.evaluate(() => {
    const value = typeof window.DUR === 'number' ? window.DUR : null;
    if (typeof window.render !== 'function') return { value, noRender: true };
    try {
      window.render(0);
      if (value !== null) window.render(value);
    } catch (e) {
      return { value, error: String(e && e.message ? e.message : e) };
    }
    return { value };
  });
  dur = report.value;
  if (report.noRender) fail('the page has no window.render(t) (see the page contract in core/render/page.mjs)', { json: true });
  if (report.error) renderError = report.error;
} finally {
  await browser.close();
  closeServer();
}

if (renderError) fail(`window.render(t) threw: ${renderError}`, { json: true });
if (dur === null || !Number.isFinite(dur)) {
  fail('the page did not set a numeric window.DUR (see the page contract in core/render/page.mjs)', { json: true });
}
if (Math.abs(dur - expected) > 1e-6) {
  fail(`window.DUR is ${dur} s but clip.json says ${expected} s`, { json: true });
}

console.log(JSON.stringify({ ok: true, dur }));
