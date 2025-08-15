// fbref_fullcopy.js
import { chromium } from 'playwright';
import fs from 'fs';

const TARGET_URL = 'https://fbref.com/en/squads/f5922ca5/2024-2025/all_comps/Huddersfield-Town-Stats-All-Competitions';

(async () => {
  console.log('🚀 Launching browser…');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log(`🌐 Visiting: ${TARGET_URL}`);
  await page.goto(TARGET_URL, { waitUntil: 'networkidle' });

  // Scroll to force FBref to load lazy tables from comment blocks
  await page.evaluate(async () => {
    for (let y = 0; y <= document.body.scrollHeight; y += 1000) {
      window.scrollTo(0, y);
      await new Promise(r => setTimeout(r, 150));
    }
  });

  // Now grab *visible text* exactly like Ctrl+A / Ctrl+C
  const visibleText = await page.evaluate(() => {
    return document.body.innerText;
  });

  fs.mkdirSync('leads', { recursive: true });
  fs.writeFileSync('leads/data.txt', visibleText, 'utf-8');

  await browser.close();
  console.log('🎉 Done! Full page text saved to leads/data.txt');
})();
