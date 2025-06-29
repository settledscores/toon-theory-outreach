import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs/promises';
import path from 'path';
import fsExtra from 'fs-extra';

puppeteer.use(StealthPlugin());

const BASE_URL = 'https://www.bbb.org/search?find_text=Accounting&find_entity=&find_type=Category&find_loc=Austin%2C+TX&find_country=USA';
const scrapedFilePath = path.join('leads', 'scraped_leads.json');

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|cpa|mba|phd|md|ceo|cto|cmo|founder|president)\b/gi];

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  const steps = randomBetween(5, 8);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(300, 800));
  }
}

function cleanBusinessName(name) {
  if (!name) return '';
  let cleaned = name;
  for (const suffix of businessSuffixes) {
    cleaned = cleaned.replace(suffix, '').trim();
  }
  return cleaned.replace(/[.,]$/, '').trim();
}

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;
  const honorifics = ['Mr\\.', 'Mrs\\.', 'Ms\\.', 'Miss', 'Dr\\.', 'Prof\\.', 'Mx\\.'];
  const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');
  let clean = raw.replace(honorificRegex, '').replace(/[,/\\]+$/, '').trim();
  let namePart = clean;
  let titlePart = '';
  if (clean.includes(',')) {
    const [name, title] = clean.split(',', 2);
    namePart = name.trim();
    titlePart = title.trim();
  }
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;
  let tokens = namePart.split(/\s+/).filter(Boolean);
  if (tokens.length > 2 && nameSuffixes.some(regex => regex.test(tokens[tokens.length - 1]))) {
    tokens.pop();
  }
  if (tokens.length < 2 || tokens.length > 4) return null;
  return {
    'first name': tokens[0],
    'middle name': tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    'last name': tokens[tokens.length - 1],
    'title': titlePart
  };
}

async function scrapeProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    console.log(`🧭 Scraping profile: ${url}`);
    await delay(randomBetween(1500, 3000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = [...document.querySelectorAll('script')].find(s => s.textContent.includes('business_name'));
      const businessNameMatch = scriptTag?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/);
      const businessName = businessNameMatch?.[1] || '';
      const website = Array.from(document.querySelectorAll('a')).find(a => a.innerText.toLowerCase().includes('visit website'))?.href || '';
      const fullText = document.body.innerText;
      const locationMatch = fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}/);
      const location = locationMatch?.[0] || '';
      const principalMatch = fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i);
      const principalContactRaw = principalMatch?.[1]?.trim() || '';
      const industryMatch = fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(t => t.trim()).join(', ') || '';
      return { businessName, principalContact: principalContactRaw, location, industry, website };
    });

    data.businessName = cleanBusinessName(data.businessName);
    const split = cleanAndSplitName(data.principalContact, data.businessName);

    if (!split || !data.website || !data.businessName) {
      console.log('⚠️ Invalid or incomplete profile. Skipping...');
      return null;
    }

    const record = {
      'business name': data.businessName,
      'website url': data.website,
      'location': data.location,
      'industry': data.industry,
      'first name': split['first name'],
      'middle name': split['middle name'],
      'last name': split['last name'],
      'title': split['title'],
      'email': '',
      'web copy': '',
      'use cases': '',
      'services': '',
      'email 1': '',
      'email 2': '',
      'email 3': '',
      'message id': '',
      'message id 2': '',
      'message id 3': '',
      'initial date': '',
      'follow-up 1 date': '',
      'follow-up 2 date': '',
      'reply': ''
    };

    console.log(`✅ Scraped ${split['first name']} ${split['middle name']} ${split['last name']} of ${data.businessName}`);
    return record;

  } catch (err) {
    console.error(`❌ Error scraping ${url}:`, err.message);
    return null;
  }
}

async function updateLeadsJson(newData) {
  console.log('📝 Updating scraped_leads.json...');
  await fsExtra.ensureDir(path.dirname(scrapedFilePath));

  let existing = { scraped_at: '', total: 0, records: [] };

  if (await fsExtra.pathExists(scrapedFilePath)) {
    try {
      const raw = await fs.readFile(scrapedFilePath, 'utf-8');
      existing = JSON.parse(raw);
      console.log(`📊 Loaded ${existing.records.length} existing records`);
    } catch (err) {
      console.warn('⚠️ Failed to parse existing JSON. Starting fresh.');
    }
  }

  const dedupeKey = `${newData['business name']}|${newData['website url']}`;
  const map = new Map(
    existing.records.map(r => [`${r['business name']}|${r['website url']}`, r])
  );

  map.set(dedupeKey, newData);
  const final = Array.from(map.values());

  await fs.writeFile(scrapedFilePath, JSON.stringify({
    scraped_at: new Date().toISOString(),
    total: final.length,
    records: final
  }, null, 2));

  console.log(`✅ Updated ${scrapedFilePath} with ${final.length} total records`);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  console.log('🔍 Visiting search page...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 0 });
  await page.waitForSelector('a[href*="/profile/"]');
  await humanScroll(page);

  const profileLinks = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href*="/profile/"]'))
      .map(a => a.href)
      .filter((href, i, arr) => !href.includes('/about') && arr.indexOf(href) === i)
  );

  console.log(`🔗 Found ${profileLinks.length} profile links.`);

  for (let i = 0; i < 3 && i < profileLinks.length; i++) {
    const link = profileLinks[i];
    const data = await scrapeProfile(page, link);
    if (data) await updateLeadsJson(data);

    const wait = randomBetween(15000, 30000);
    console.log(`⏳ Waiting ${Math.floor(wait / 1000)}s...`);
    await delay(wait);
  }

  await browser.close();
  console.log('✅ Scraping complete.');
})();
