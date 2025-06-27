import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();
puppeteer.use(StealthPlugin());

// 🟩 Scraper Targets
const NICHES = [
  "https://www.bbb.org/search?find_text=Legal+Services&find_entity=&find_type=&find_loc=San+Diego%2C+CA&find_country=USA",
  "https://www.bbb.org/search?find_text=Management+Consultant&find_entity=60533-000&find_type=Category&find_loc=San+Diego%2C+CA&find_country=USA",
  "https://www.bbb.org/search?find_text=Management+Consultant&find_entity=&find_type=&find_loc=Detroit%2C+MI&find_country=USA",
  "https://www.bbb.org/search?find_text=Staffing+Agencies&find_entity=&find_type=&find_loc=Washington%2C+PA&find_country=USA",
  "https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Boston%2C+MA&find_country=USA"
];

// 🟩 Static Variables
const API_KEY = 'UtubR5TLlqxOZOAmodTkqjAyImTpXyYlTYFVXM2p';
const BASE_URL = 'https://app.nocodb.com';
const TABLE_ID = 'ms0nic0srwe82cw';
const VIEW_ID = 'vw5b7hiliawyo6eo';

// 🟩 Utility
const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

// 🟩 Human scroll simulation
async function humanScroll(page) {
  for (let i = 0; i < randomBetween(5, 8); i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(300, 800));
  }
}

// 🟩 Name cleaning helpers
function cleanBusinessName(name) {
  return name?.replace(/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i, '').replace(/[.,]$/, '').trim();
}

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;
  const honorificRegex = /^(Mr\.|Mrs\.|Ms\.|Miss|Dr\.|Prof\.|Mx\.)\s+/i;
  let clean = raw.replace(honorificRegex, '').replace(/[,/\\]+$/, '').trim();
  let namePart = clean, titlePart = '';
  if (clean.includes(',')) [namePart, titlePart] = clean.split(',').map(s => s.trim());
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;

  const tokens = namePart.split(/\s+/);
  if (tokens.length < 2 || tokens.length > 4) return null;

  return {
    firstName: tokens[0],
    middleName: tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    lastName: tokens[tokens.length - 1],
    title: titlePart
  };
}

// 🟩 BBB Profile Extractor
async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(1500, 3000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = [...document.querySelectorAll('script')].find(s => s.textContent.includes('"business_name"'));
      const businessName = scriptTag?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/)?.[1] || '';
      const website = [...document.querySelectorAll('a')].find(a => a.innerText.toLowerCase().includes('visit website') && a.href.startsWith('http'))?.href || '';
      const fullText = document.body.innerText;

      return {
        businessName,
        principalContact: fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i)?.[1]?.trim() || '',
        location: fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}(-\d{4})?/)?.[0] || '',
        years: fullText.match(/Business Started:\s*(.+)/i)?.[1]?.split('\n')[0].trim() || '',
        industry: fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i)?.[1]?.split('\n').map(t => t.trim()).join(', ') || '',
        website
      };
    });

    data.businessName = cleanBusinessName(data.businessName);
    const split = cleanAndSplitName(data.principalContact, data.businessName);
    if (!split || !data.website || !data.businessName) return null;

    return {
      ...data,
      ...split,
      profileLink: url
    };
  } catch (err) {
    console.error(`❌ Failed to extract: ${url} — ${err.message}`);
    return null;
  }
}

// 🟩 NocoDB Connectivity Test
async function verifyNocoDBConnection() {
  const url = `${BASE_URL}/api/v2/tables/${TABLE_ID}/records?offset=0&limit=1&viewId=${VIEW_ID}`;
  try {
    const res = await axios.get(url, { headers: { 'xc-token': API_KEY } });
    console.log(`✅ NocoDB test passed — ${res.data?.list?.length} records accessible`);
    return true;
  } catch (err) {
    console.error(`❌ NocoDB connection failed:`, err.response?.data || err.message);
    return false;
  }
}

// 🟩 POST to NocoDB
async function syncToNocoDB(record) {
  const url = `${BASE_URL}/api/v1/db/data/v1/wbv4do3x/${TABLE_ID}`;
  const body = {
    business_name: record.businessName,
    website_url: record.website,
    location: record.location,
    industry: record.industry,
    years: record.years,
    first_name: record.firstName,
    middle_name: record.middleName,
    last_name: record.lastName,
    decision_maker_title: record.title,
    profile_link: record.profileLink
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'xc-auth': API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();
    if (!res.ok) {
      console.error(`❌ NocoDB error (${res.status}): ${JSON.stringify(data)}`);
    } else {
      console.log(`✅ Synced: ${record.businessName}`);
    }
  } catch (err) {
    console.error(`❌ NocoDB sync failed: ${err.message}`);
  }
}

// 🟩 Main Runner
(async () => {
  if (!(await verifyNocoDBConnection())) return;

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const seen = new Set();
  const deduped = new Set();

  for (const baseUrl of NICHES) {
    console.log(`🔍 Scraping niche: ${baseUrl}`);
    let pageNum = 1, validCount = 0, consecutiveEmpty = 0;

    while (validCount < 20 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);

      const links = await page.evaluate(() =>
        [...document.querySelectorAll('a[href*="/profile/"]')].map(a => a.href).filter((href, i, arr) => arr.indexOf(href) === i)
      );

      if (!links.length) break;

      let scrapedThisPage = 0;
      for (const link of links) {
        if (seen.has(link)) continue;
        seen.add(link);

        const profile = await extractProfile(page, link);
        if (profile) {
          const dedupKey = `${profile.businessName.toLowerCase()}|${profile.website.toLowerCase()}`;
          if (!deduped.has(dedupKey)) {
            deduped.add(dedupKey);
            await syncToNocoDB(profile);
            validCount++;
            scrapedThisPage++;
          }
        }

        await delay(randomBetween(3000, 6000));
        if (validCount >= 20) break;
      }

      consecutiveEmpty = scrapedThisPage === 0 ? consecutiveEmpty + 1 : 0;
      pageNum++;
    }

    console.log(`🏁 Finished: ${baseUrl} — ${validCount} saved`);
  }

  await browser.close();
  console.log('✅ All niches done.');
})();
