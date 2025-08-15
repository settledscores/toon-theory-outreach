import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import * as cheerio from 'cheerio';
import fs from 'fs';

puppeteer.use(StealthPlugin());

const TARGET_URL = 'https://fbref.com/en/squads/f5922ca5/2024-2025/all_comps/Huddersfield-Town-Stats-All-Competitions';

// ✅ Correct IDs for the *All Competitions* page
const TABLE_IDS = [
  'stats_standard_combined',     // Standard Stats
  'matchlogs_for',               // Scores & Fixtures
  'stats_keeper_combined',       // Goalkeeping
  'stats_shooting_combined',     // Shooting
  'stats_playing_time_combined', // Playing Time
  'stats_misc_combined',         // Miscellaneous
  'stats_player_summary',        // Player Summary  (commented)
  'stats_keeper_summary'         // GK Summary      (commented)
];

// Convert one FBref table HTML to TSV, aligning by data-stat keys
function tableHtmlToTSV(tableHtml) {
  const $ = cheerio.load(tableHtml);

  // use the last thead row with actual labels
  const headerRows = $('thead tr');
  let header = headerRows.last();
  if (header.hasClass('over_header') && headerRows.length > 1) {
    header = headerRows.eq(headerRows.length - 2);
  }

  // column order + keys (data-stat)
  const cols = [];
  header.find('th,td').each((_, cell) => {
    const $cell = $(cell);
    const key = $cell.attr('data-stat') || '';
    const name = $cell.text().replace(/\s+/g, ' ').trim();
    if (name || key) cols.push({ key, name: name || key || '' });
  });

  const headerLine = cols.map(c => c.name).join('\t');
  const lines = [headerLine];

  $('tbody tr').each((_, tr) => {
    const $tr = $(tr);
    if ($tr.hasClass('thead')) return; // skip header repeat rows

    const row = cols.map(({ key }) => {
      let txt = '';
      if (!key) {
        txt = $tr.find('th,td').first().text();
      } else if (key === 'player') {
        const $cell = $tr.find('th[data-stat="player"]');
        txt = $cell.find('a').first().text() || $cell.text(); // full name
      } else {
        const $cell = $tr.find(`td[data-stat="${key}"]`);
        txt = $cell.text();
      }
      return txt.replace(/\s+/g, ' ').trim();
    });

    if (row.every(v => v === '')) return;
    lines.push(row.join('\t'));
  });

  return lines.join('\n');
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
  await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 120000 });

  await page.waitForSelector('div[data-template="Partials/Teams/Summary"]', { timeout: 20000 });

  console.log('📋 Extracting summary...');
  const summaryData = await page.evaluate(() => {
    const el = document.querySelector('div[data-template="Partials/Teams/Summary"]');
    const title = el?.querySelector('h1 span')?.textContent?.trim() || '';
    const lines = Array.from(el?.querySelectorAll('p') || []).map(p => p.innerText.trim());
    return { title, lines };
  });

  // Get table HTML whether visible or wrapped in an HTML comment under #all_<id>
  async function getTableHtml(id) {
    const live = await page.$(`table#${id}`);
    if (live) return page.$eval(`table#${id}`, el => el.outerHTML);

    const wrapperSel = `#all_${id}`;
    const wrapper = await page.$(wrapperSel);
    if (!wrapper) return '';

    const html = await page.$eval(wrapperSel, el => {
      const w = document.createTreeWalker(el, NodeFilter.SHOW_COMMENT, null);
      let n = w.nextNode();
      while (n) {
        const txt = n.data || '';
        if (txt.includes('<table') && txt.includes(`id="${el.id.replace('all_', '')}"`)) {
          return txt;
        }
        n = w.nextNode();
      }
      return '';
    });
    return html;
  }

  console.log('📊 Extracting tables (All Competitions)...');
  const out = [];
  out.push('=== SUMMARY ===');
  out.push(summaryData.title);
  out.push('');
  summaryData.lines.forEach(l => out.push(l));
  out.push('');
  out.push('=== TABLES (All Competitions) ===');

  for (const id of TABLE_IDS) {
    let html = await getTableHtml(id);
    if (!html) {
      console.warn(`⚠ Table not found: ${id}`);
      out.push(`\n--- ${id} (NOT FOUND) ---`);
      continue;
    }
    // if it came from a comment, strip markers
    html = html.replace(/^<!--\s*|\s*-->$/g, '');
    const tsv = tableHtmlToTSV(html);
    out.push(`\n--- ${id} ---\n${tsv}`);
    console.log(`✅ Parsed: ${id}`);
  }

  fs.mkdirSync('leads', { recursive: true });
  fs.writeFileSync('leads/data.txt', out.join('\n'), 'utf-8');

  await browser.close();
  console.log('🎉 Done! Saved to leads/data.txt');
})();
