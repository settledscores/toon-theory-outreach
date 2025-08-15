import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import { load } from 'cheerio';

puppeteer.use(StealthPlugin());

const TARGET_URL = 'https://fbref.com/en/squads/f5922ca5/2024-2025/all_comps/Huddersfield-Town-Stats-All-Competitions';

// All "All Competitions" tables we want
const TABLE_IDS = [
  'stats_standard_combined',        // Standard Stats
  'matchlogs_for',                   // Scores & Fixtures
  'stats_keeper_combined',           // Goalkeeping
  'stats_shooting_combined',         // Shooting
  'stats_playing_time_combined',     // Playing Time
  'stats_misc_combined',             // Misc Stats
  'stats_summary_combined',          // Player Summary
  'stats_keeper_summary_combined'    // Goalkeeper Summary
];

// Convert HTML table to TSV plain text
function tableToTSV(table) {
  let rows = [];
  table.find('tr').each((_, row) => {
    let cells = [];
    table.find(row).children('th, td').each((_, cell) => {
      let text = table.find(cell).text().trim().replace(/\s+/g, ' ');
      cells.push(text);
    });
    if (cells.length > 0) rows.push(cells.join('\t'));
  });
  return rows.join('\n');
}

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

  // FBref hides tables in HTML comments → remove them
  const html = await page.content();
  const uncommentedHtml = html.replace(/<!--/g, '').replace(/-->/g, '');
  const $ = load(uncommentedHtml);

  // Extract summary block
  console.log('📋 Extracting summary...');
  const summaryBlock = $('div[data-template="Partials/Teams/Summary"]');
  const title = summaryBlock.find('h1 span').first().text().trim();
  const summaryLines = summaryBlock.find('p').map((_, p) => $(p).text().trim()).get();

  // Extract each table
  console.log('📊 Extracting tables...');
  const tablesData = {};
  for (const tableId of TABLE_IDS) {
    const table = $(`table#${tableId}`);
    if (table.length) {
      tablesData[tableId] = tableToTSV(table);
      console.log(`✅ Found table: ${tableId}`);
    } else {
      tablesData[tableId] = '';
      console.warn(`⚠ Table not found: ${tableId}`);
    }
  }

  // Save as plain text
  console.log('💾 Saving data to data.txt...');
  let output = '';
  output += `=== SUMMARY ===\n${title}\n\n`;
  summaryLines.forEach(line => output += `${line}\n`);
  output += `\n=== TABLES (All Competitions) ===\n`;
  for (const [id, tsv] of Object.entries(tablesData)) {
    output += `\n--- ${id} ---\n${tsv}\n`;
  }
  fs.writeFileSync('leads/data.txt', output, 'utf-8');

  await browser.close();
  console.log('🎉 Done! Data saved to leads/data.txt');
})();
