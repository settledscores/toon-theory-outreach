import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { load } from 'cheerio';
import fs from 'fs';

puppeteer.use(StealthPlugin());

const TARGET_URL =
  'https://fbref.com/en/squads/f5922ca5/2024-2025/all_comps/Huddersfield-Town-Stats-All-Competitions';

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

  // Get the rendered HTML after JS loads
  const html = await page.content();
  const $ = load(html);

  console.log('📋 Extracting summary...');
  const summaryContainer = $('div[data-template="Partials/Teams/Summary"]');
  const summaryTitle = summaryContainer.find('h1 span').first().text().trim();
  const summaryDetails = summaryContainer
    .find('p')
    .map((_, p) => $(p).text().trim())
    .get();

  console.log('📊 Extracting tables...');
  const tablesData = {};

  for (const tableId of TABLE_IDS) {
    // FBref sometimes hides tables inside HTML comments, so check and parse them too
    let tableElement = $(`table#${tableId}`);
    if (!tableElement.length) {
      $('*')
        .contents()
        .each((_, el) => {
          if (el.type === 'comment' && el.data.includes(`<table id="${tableId}"`)) {
            const $comment = load(el.data);
            if ($comment(`table#${tableId}`).length) {
              tableElement = $comment(`table#${tableId}`);
            }
          }
        });
    }

    if (tableElement.length) {
      // Convert table to plain text (TSV format)
      const rows = [];
      tableElement.find('tr').each((_, row) => {
        const cells = [];
        $(row)
          .find('th, td')
          .each((_, cell) => {
            cells.push($(cell).text().trim());
          });
        if (cells.length > 0) rows.push(cells.join('\t'));
      });
      tablesData[tableId] = rows.join('\n');
      console.log(`✅ Found table: ${tableId}`);
    } else {
      console.warn(`⚠ Table not found: ${tableId}`);
      tablesData[tableId] = '';
    }
  }

  console.log('💾 Saving data to data.txt...');
  let output = '';
  output += `=== SUMMARY ===\n${summaryTitle}\n\n`;
  summaryDetails.forEach(line => {
    output += `${line}\n`;
  });
  output += `\n=== TABLES ===\n`;
  for (const [id, text] of Object.entries(tablesData)) {
    output += `\n--- ${id} ---\n${text}\n`;
  }

  fs.writeFileSync('leads/data.txt', output, 'utf-8');

  await browser.close();
  console.log('🎉 Done! Data saved to leads/data.txt');
})();
