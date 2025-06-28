import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';

puppeteer.use(StealthPlugin());

// Load environment variables
const BASE_URL = process.env.SEATABLE_BASE_URL;
const API_KEY = process.env.SEATABLE_API_KEY;
const BASE_UUID = process.env.SEATABLE_BASE_UUID;
const TABLE_NAME = process.env.SEATABLE_SCRAPER_TABLE_NAME;

const NICHES = [
  "https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Boston%2C+MA&find_country=USA"
];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|cpa|mba|phd|md|ceo|cto|cmo|founder|president)\b/gi];

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
    if (!split || !data.website || !data.businessName) return null;

    return {
      "business name": data.businessName,
      "website url": data.website,
      "location": data.location,
      "industry": data.industry,
      "First Name": split.firstName,
      "Middle Name": split.middleName,
      "Last Name": split.lastName,
      "Decision Maker Title": split.title
    };
  } catch (err) {
    console.error(`❌ Failed to extract: ${url} — ${err.message}`);
    return null;
  }
}

async function syncToSeaTable(records) {
  const url = `${BASE_URL}/api/v2/dtable-db/dtables/${BASE_UUID}/tables/${encodeURIComponent(TABLE_NAME)}/records/batch/`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${API_KEY}`, // using direct base token
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ records })
  });

  if (!res.ok) {
    const text = await res.text();
    console.error(`❌ SeaTable API error (${res.status}):`, text);
    throw new Error(text);
  } else {
    console.log(`✅ Synced ${records.length} records to SeaTable`);
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

  for (const baseUrl of NICHES) {
    let pageNum = 1;
    let validCount = 0;
    let consecutiveEmpty = 0;

    while (validCount < 3 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);

      const links = await page.evaluate(() => [...document.querySelectorAll('a[href*="/profile/"]')].map(a => a.href));
      if (!links.length) break;

      let scrapedThisPage = 0;
      for (const link of links) {
        if (seen.has(link)) continue;
        seen.add(link);
        const profile = await extractProfile(page, link);
        if (profile) {
          const key = `${profile["business name"].toLowerCase()}|${profile["website url"].toLowerCase()}`;
          if (!deduped.has(key)) {
            deduped.add(key);
            allRecords.push(profile);
            console.log('📦', profile);
            validCount++;
            scrapedThisPage++;
          }
        }
        await delay(randomBetween(3000, 6000));
        if (validCount >= 3) break;
      }
      consecutiveEmpty = scrapedThisPage === 0 ? consecutiveEmpty + 1 : 0;
      pageNum++;
    }
    console.log(`🏁 Finished: ${baseUrl} — ${validCount} saved`);
  }

  await browser.close();
  console.log(`📤 Sending ${allRecords.length} total records to SeaTable...`);
  await syncToSeaTable(allRecords);
  console.log('✅ All niches done.');
})();
