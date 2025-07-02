import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs/promises';
import path from 'path';
import fsExtra from 'fs-extra';

puppeteer.use(StealthPlugin());

const SEARCH_URLS = [
  'https://www.bbb.org/search?find_text=Accounting&find_entity=&find_type=Category&find_loc=Austin%2C+TX&find_country=USA',
  'https://www.bbb.org/search?find_text=Business+Development&find_entity=60170-110&find_type=Category&find_loc=Bloomington%2C+IN&find_country=USA',
  'https://www.bbb.org/search?find_text=business+tax+consultant&find_entity=60858-000&find_type=Category&find_loc=Santa+Ana%2C+CA&find_country=USA',
  'https://www.bbb.org/search?find_text=Business+Development&find_entity=60170-110&find_type=Category&find_loc=Chicago%2C+IL&find_country=USA',
  'https://www.bbb.org/search?find_text=Financial+Consultants&find_entity=&find_type=&find_loc=Brooklyn%2C+NY&find_country=USA',
  'https://www.bbb.org/search?find_text=Business+Development&find_entity=60170-110&find_type=Category&find_loc=Santa+Barbara%2C+CA&find_country=USA',
  'https://www.bbb.org/us/la/new-orleans/category/tax-consultant',
  'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Minneapolis%2C+MN&find_country=USA',
  'https://www.bbb.org/us/mn/minneapolis/category/tax-consultant',
  'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Tinton+Falls%2C+NJ&find_country=USA',
];

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

    return record;

  } catch (err) {
    console.error(`❌ Error scraping ${url}:`, err.message);
    return null;
  }
}

async function updateLeadsJson(newData, existingMap) {
  const dedupeKey = `${newData['business name']}|${newData['website url']}`;
  if (existingMap.has(dedupeKey)) return false;

  existingMap.set(dedupeKey, newData);

  const records = Array.from(existingMap.values());
  await fs.writeFile(scrapedFilePath, JSON.stringify({
    scraped_at: new Date().toISOString(),
    total: records.length,
    records
  }, null, 2));

  return true;
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  await fsExtra.ensureDir(path.dirname(scrapedFilePath));

  let existingMap = new Map();

  if (await fsExtra.pathExists(scrapedFilePath)) {
    try {
      const raw = await fs.readFile(scrapedFilePath, 'utf-8');
      const existing = JSON.parse(raw);
      for (const rec of existing.records) {
        const key = `${rec['business name']}|${rec['website url']}`;
        existingMap.set(key, rec);
      }
      console.log(`📂 Loaded ${existingMap.size} previously scraped records.`);
    } catch {
      console.warn('⚠️ Failed to parse existing JSON. Starting fresh.');
    }
  }

  for (const baseUrl of SEARCH_URLS) {
    let newScraped = 0;
    let currentUrl = baseUrl;

    while (newScraped < 11 && currentUrl) {
      await page.goto(currentUrl, { waitUntil: 'networkidle2', timeout: 0 });
      await page.waitForSelector('a[href*="/profile/"]', { timeout: 10000 });
      await humanScroll(page);

      const profileLinks = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href*="/profile/"]'))
          .map(a => a.href)
          .filter((href, i, arr) => !href.includes('/about') && arr.indexOf(href) === i)
      );

      for (const link of profileLinks) {
        if (newScraped >= 11) break;

        const data = await scrapeProfile(page, link);
        if (data) {
          const added = await updateLeadsJson(data, existingMap);
          if (added) {
            newScraped++;
            console.log(`✅ Added: ${data['business name']}`);
          } else {
            console.log(`⏭️ Skipped duplicate: ${data['business name']}`);
          }
        }

        const wait = randomBetween(15000, 30000);
        console.log(`⏳ Waiting ${Math.floor(wait / 1000)}s...`);
        await delay(wait);
      }

      const nextPageUrl = await page.evaluate(() => {
        const nextBtn = document.querySelector('a[rel="next"], a.pagination__next');
        return nextBtn ? nextBtn.href : null;
      });

      if (!nextPageUrl || newScraped >= 11) break;
      currentUrl = nextPageUrl;
    }

    console.log(`📌 Done with ${baseUrl} — Added ${newScraped} new profiles`);
  }

  await browser.close();
  console.log(`✅ All scraping complete.`);
})();
