import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import { load } from 'cheerio';

puppeteer.use(StealthPlugin());

const TARGET_URL = 'https://fbref.com/en/squads/f5922ca5/2024-2025/all_comps/Huddersfield-Town-Stats-All-Competitions';

const TABLE_IDS = [
  'matchlogs_for',
  'matchlogs_against',
  'stats_keeper_11',
  'stats_keeper_adv_11',
  'stats_shooting_11',
  'stats_passing_11',
  'stats_passing_types_11',
  'stats_gca_11',
  'stats_defense_11',
  'stats_possession_11',
  'stats_playing_time_11',
  'stats_misc_11'
];

(async () => {
  console.log('🚀 Launching browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  console.log(`🌐 Visiting: ${TARGET_URL}`);
  await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 90000 });

  // Wait for summary block to load
  await page.waitForSelector('div[data-template="Partials/Teams/Summary"]', { timeout: 15000 });

  console.log('📋 Extracting summary...');
  const summaryData = await page.evaluate(() => {
    const container = document.querySelector('div[data-template="Partials/Teams/Summary"]');
    if (!container) return {};
    const title = container.querySelector('h1 span')?.innerText || '';
    const paras = Array.from(container.querySelectorAll('p')).map(p => p.innerText.trim());
    return { title, details: paras };
  });

  console.log('📄 Getting full HTML with comments...');
  const rawHTML = await page.content();

  // Remove comment tags so hidden tables become visible
  const uncommentedHTML = rawHTML.replace(/<!--/g, '').replace(/-->/g, '');

  // Parse with cheerio
  const $ = load(uncommentedHTML);

  console.log('📊 Extracting tables...');
  const tablesData = {};
  for (const tableId of TABLE_IDS) {
    const table = $(`table#${tableId}`);
    if (table.length) {
      tablesData[tableId] = table.html();
      console.log(`✅ Found table: ${tableId}`);
    } else {
      tablesData[tableId] = '';
      console.warn(`⚠ Table not found: ${tableId}`);
    }
  }

  console.log('💾 Saving data to data.txt...');
  let output = '';
  output += `=== SUMMARY ===\n${summaryData.title}\n\n`;
  summaryData.details.forEach(line => { output += `${line}\n`; });
  output += `\n=== TABLES ===\n`;
  for (const [id, html] of Object.entries(tablesData)) {
    output += `\n--- ${id} ---\n${html}\n`;
  }
  fs.writeFileSync('leads/data.txt', output, 'utf-8');

  await browser.close();
  console.log('🎉 Done! Data saved to leads/data.txt');
})();
