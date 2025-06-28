import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();
puppeteer.use(StealthPlugin());

const API_KEY = process.env.SEATABLE_API_KEY;
const BASE_UUID = 'd603f65e-b769-448c-b7c8-4f155c3f38b0';
const TABLE_NAME = 'Scraper Leads';
const BASE_URL = 'https://cloud.seatable.io';

const NICHES = [
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Boston%2C+MA&find_country=USA'
];

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|cpa|mba|jd|phd|md|cfa|cfe|cma|cfp|llb|llm|rn|np|pa|pmp|pe|cis|cissp|shrm|phr|sphr|gphr|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|president|founder|ceo|cto|cmo|chro)\b\.?/gi];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  for (let i = 0; i < randomBetween(5, 8); i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(300, 800));
  }
}

function cleanBusinessName(name) {
  if (!name) return '';
  for (const suffix of businessSuffixes) name = name.replace(suffix, '').trim();
  return name.replace(/[.,]$/, '').trim();
}

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;
  const honorifics = ['Mr\\.', 'Mrs\\.', 'Ms\\.', 'Dr\\.', 'Prof\\.', 'Mx\\.'];
  const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');
  let clean = raw.replace(honorificRegex, '').replace(/[,/\\]+$/, '').trim();
  let namePart = clean, titlePart = '';
  if (clean.includes(',')) [namePart, titlePart] = clean.split(',', 2).map(s => s.trim());
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;
  let tokens = namePart.split(/\s+/).filter(Boolean);
  if (tokens.length > 2 && nameSuffixes.some(rx => rx.test(tokens[tokens.length - 1]))) tokens.pop();
  if (tokens.length < 2 || tokens.length > 4) return null;
  return {
    firstName: tokens[0],
    middleName: tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    lastName: tokens[tokens.length - 1],
    title: titlePart
  };
}

async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(1500, 3000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const script = [...document.querySelectorAll('script')].find(s => s.textContent.includes('"business_name"'));
      const businessName = script?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/)?.[1] || '';
      const website = [...document.querySelectorAll('a')]
        .find(a => a.innerText.toLowerCase().includes('visit website') && a.href.includes('http'))?.href || '';
      const txt = document.body.innerText;
      const location = txt.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}(?:-\d{4})?/)?.[0] || '';
      const principal = txt.match(/Principal Contacts\s+(.*?)(\n|$)/i)?.[1]?.trim() || '';
      const industry = txt.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i)?.[1]?.split('\n').map(s => s.trim()).join(', ') || '';
      return { businessName, principalContact: principal, location, industry, website };
    });

    data.businessName = cleanBusinessName(data.businessName);
    const nameParts = cleanAndSplitName(data.principalContact, data.businessName);
    if (!nameParts || !data.website || !data.businessName) return null;

    return {
      'business name': data.businessName,
      'website url': data.website,
      location: data.location,
      industry: data.industry,
      'First Name': nameParts.firstName,
      'Middle Name': nameParts.middleName,
      'Last Name': nameParts.lastName,
      'Decision Maker Title': nameParts.title
    };
  } catch (err) {
    console.error(`❌ Failed to extract: ${url} — ${err.message}`);
    return null;
  }
}

async function getSeaTableAccessToken() {
  const url = `${BASE_URL}/api/v2.1/dtable/app-access-token/`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Token ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ dtable_uuid: BASE_UUID })
  });
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status}`);
  const json = await res.json();
  return json.access_token;
}

async function syncToSeaTable(records) {
  try {
    const token = await getSeaTableAccessToken();
    const url = `${BASE_URL}/dtable-db/api/v1/dtables/${BASE_UUID}/tables/${encodeURIComponent(TABLE_NAME)}/records/batch/`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ records })
    });
    const result = await res.json();
    if (!res.ok) console.error(`❌ SeaTable error (${res.status}): ${JSON.stringify(result)}`);
    else console.log(`✅ Synced ${records.length} records to SeaTable`);
  } catch (err) {
    console.error(`❌ SeaTable sync failed: ${err.message}`);
  }
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const seen = new Set();
  const deduped = new Set();
  const allRecords = [];

  for (const niche of NICHES) {
    console.log(`🔍 Scraping niche: ${niche}`);
    let pageNum = 1;
    let validCount = 0;
    let consecutiveEmpty = 0;

    while (validCount < 3 && consecutiveEmpty < 5) {
      const pageUrl = niche.includes('page=') ? niche.replace(/page=\d+/, `page=${pageNum}`) : `${niche}&page=${pageNum}`;
      await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);

      const links = await page.evaluate(() =>
        [...document.querySelectorAll('a[href*="/profile/"]')]
          .map(a => a.href)
          .filter((href, i, arr) => arr.indexOf(href) === i)
      );

      if (!links.length) break;

      let scraped = 0;
      for (const link of links) {
        if (seen.has(link)) continue;
        seen.add(link);
        const profile = await extractProfile(page, link);
        if (profile) {
          const key = `${profile['business name'].toLowerCase()}|${profile['website url'].toLowerCase()}`;
          if (!deduped.has(key)) {
            deduped.add(key);
            allRecords.push(profile);
            console.log('📦', profile);
            validCount++;
            scraped++;
          }
        }
        await delay(randomBetween(3000, 6000));
        if (validCount >= 3) break;
      }

      consecutiveEmpty = scraped === 0 ? consecutiveEmpty + 1 : 0;
      pageNum++;
    }

    console.log(`🏁 Finished: ${niche} — ${validCount} saved`);
  }

  await browser.close();
  console.log(`📤 Sending ${allRecords.length} total records to SeaTable...`);
  await syncToSeaTable(allRecords);
  console.log('✅ All niches done.');
})();
