// Pixel regression: the Art Deco marquee must render and animate inside its registered box at both supported review aspects.
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDemo, closeServer } from '../../.agents/skills/lemo/library/core/render/page.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const clipDir = path.join(repoRoot, '.agents/skills/lemo/samples/clips/art-deco');

try {
  for (const [w, h] of [[1920, 1080], [1080, 1920]]) {
    const { browser, page } = await openDemo(clipDir, { w, h });
    try {
      const result = await page.evaluate(() => {
        const canvas = document.querySelector('#c');
        const ctx = canvas.getContext('2d');
        window.render(0.9); // before the first bulb lights
        const before = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        window.render(4.8); // after all letters have lit
        const after = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        const texts = window.TEXTS(4.8);
        const sign = texts.find(block => block.id === 'sign');
        const title = texts.find(block => block.id === 'title');
        const x0 = Math.max(0, Math.floor(sign.x0));
        const y0 = Math.max(0, Math.floor(sign.y0));
        const x1 = Math.min(canvas.width, Math.ceil(sign.x1));
        const y1 = Math.min(canvas.height, Math.ceil(sign.y1));
        let goldChanged = 0;
        let boxGoldAfter = 0;
        let overlappingTitleGold = 0;

        for (let y = y0; y < y1; y++) {
          for (let x = x0; x < x1; x++) {
            const i = (y * canvas.width + x) * 4;
            const isGold = after[i] > 100 && after[i] > after[i + 2] * 1.25;
            const change = Math.abs(before[i] - after[i])
              + Math.abs(before[i + 1] - after[i + 1])
              + Math.abs(before[i + 2] - after[i + 2]);
            if (isGold) {
              boxGoldAfter++;
              if (x >= title.x0 && x <= title.x1 && y >= title.y0 && y <= title.y1) {
                overlappingTitleGold++;
              }
            }
            if (change > 28 && isGold) goldChanged++;
          }
        }
        return { signText: sign.text, boxGoldAfter, goldChanged, overlappingTitleGold };
      });

      console.log(`${w}x${h}: ${JSON.stringify(result)}`);
      assert.equal(result.signText, 'THE AURELIA', `${w}x${h}: registered marquee text`);
      assert.ok(result.goldChanged > 200, `${w}x${h}: marquee did not visibly light`);
      assert.ok(result.boxGoldAfter > 500, `${w}x${h}: marquee has too few visible gold pixels`);
      assert.ok(result.overlappingTitleGold < result.boxGoldAfter * 0.25,
        `${w}x${h}: marquee registration substantially overlaps the title panel`);
    } finally {
      await browser.close();
    }
  }
} finally {
  closeServer();
}
