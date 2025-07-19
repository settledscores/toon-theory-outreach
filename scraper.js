import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import fsPromises from 'fs/promises';
import fsExtra from 'fs-extra';
import path from 'path';

puppeteer.use(StealthPlugin());

const SEARCH_URLS = [
  'https://www.bbb.org/search?find_country=CAN&find_entity=60172-000&find_id=1214_3100-800&find_latlng=49.282689%2C-123.123713&find_loc=Vancouver%2C%20BC&find_text=Business%20Consultants&find_type=Category&page=1&touched=2',
  'https://www.bbb.org/search?find_text=Business+Consultants&find_entity=&find_type=&find_loc=Toronto%2C+ON&find_country=CAN',
  'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Vancouver%2C+BC&find_country=CAN',
  'https://www.bbb.org/search?find_text=Accounting&find_entity=&find_type=&find_loc=Toronto%2C+ON&find_country=CAN',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=60509-000&find_type=Category&find_loc=Vancouver%2C+BC&find_country=CAN',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=&find_type=&find_loc=Toronto%2C+ON&find_country=CAN',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=60451-000&find_type=Category&find_loc=Toronto%2C+ON&find_country=CAN',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Vancouver%2C+BC&find_country=CAN',
  'https://www.bbb.org/search?find_text=tax+consulting&find_entity=60858-000&find_type=Category&find_loc=Vancouver%2C+BC&find_country=CAN',
  'https://www.bbb.org/search?find_text=tax+consulting&find_entity=&find_type=&find_loc=Toronto%2C+ON&find_country=CAN'
];

const leadsPath = path.join('leads', 'scraped_leads.ndjson');
const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

// Business suffixes to trim from company names
const businessSuffixes = [
  /\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i
];

// Honorifics regex to remove prefixes like Mr., Dr., etc.
const honorifics = [
  'Mr\\.',
  'Mrs\\.',
  'Ms\\.',
  'Miss',
  'Dr\\.',
  'Prof\\.',
  'Mx\\.'
];
const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');

// Name suffixes to remove from person names like Jr, Sr, CPA, MBA etc.
const nameSuffixes = [
  /\b(jr|sr|i{1,3}|iv|v|esq|esquire|cpa|mba|jd|j\.d\.|phd|m\.d\.|md|cfa|cfe|cma|cfp|llb|ll\.b\.|llm|ll\.m\.|rn|np|pa|pmp|pe|p\.eng|cis|cissp|aia|shrm[-\s]?(cp|scp)|phr|sphr|gphr|ra|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|pcc|acc|mcc|six\s?sigma|ceo|cto|cmo|chro|ret\.?|gen\.?|col\.?|maj\.?|capt?\.?|lt\.?|usa|usaf|usmc|usn|uscg|comp?tia|aws|hon|rev|fr|rabbi|imam|president|founder)\b\.?/gi
];

// Store all leads in-memory map keyed by website URL to avoid duplicates
const allLeads = new Map();

// Load existing leads from NDJSON file into allLeads map
async function loadExistingLeads() {
  if (!fs.existsSync(leadsPath)) return;
  const content = await fsPromises.readFile(leadsPath, 'utf-8');
  // Split by double newlines to separate JSON blocks
  const blocks = content.split(/\n\s*\n/);
  for (const block of blocks) {
    if (!block.trim()) continue;
    try {
      const record = JSON.parse(block);
      const url = record['website url'];
      if (url) allLeads.set(url, record);
    } catch {
      console.warn('⚠ Skipping invalid NDJSON block');
    }
  }
  console.log(`🔁 Loaded ${allLeads.size} existing leads`);
}

// Clean business name by removing suffixes and trailing punctuation
function cleanBusinessName(name) {
  if (!name) return '';
  let cleaned = name;
  for (const suffix of businessSuffixes) {
    cleaned = cleaned.replace(suffix, '').trim();
  }
  return cleaned.replace(/[.,]$/, '').trim();
}

// Parse and split raw principal contact name, remove honorifics & suffixes
function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;

  // Remove leading honorifics like Mr., Dr., etc.
  let clean = raw.replace(honorificRegex, '');

  // Remove trailing commas or slashes
  clean = clean.replace(/[,/\\]+$/, '').trim();

  let namePart = clean;
  let titlePart = '';

  // If there's a comma, split into name and title
  if (clean.includes(',')) {
    const [name, title] = clean.split(',', 2);
    namePart = name.trim();
    titlePart = title.trim();
  }

  // Avoid returning if name is same as business name (case insensitive)
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;

  let tokens = namePart.split(/\s+/).filter(Boolean);

  // Reject if name too short or too long
  if (tokens.length < 2 || tokens.length > 4) return null;

  // Remove suffixes if last token matches known suffixes and name has >2 tokens
  if (tokens.length > 2 && nameSuffixes.some(regex => regex.test(tokens[tokens.length - 1]))) {
    tokens.pop();
  }

  return {
    'first name': tokens[0],
    'middle name': tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    'last name': tokens[tokens.length - 1],
    'title': titlePart
  };
}

// Scroll the page in a human-like way with random mouse movements and scrolls
async function humanScroll(page) {
  const steps = randomBetween(5, 8);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(150, 500));
  }
}

// Scrape a profile page and extract relevant data, cleaning names and URLs
async function scrapeProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    console.log(`🧭 Scraping: ${url}`);
    await delay(randomBetween(1000, 2500));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = [...document.querySelectorAll('script')].find(s => s.textContent.includes('business_name'));
      const businessNameMatch = scriptTag?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/);
      const businessName = businessNameMatch?.[1] || '';

      const website = Array.from(document.querySelectorAll('a'))
        .find(a => a.innerText.toLowerCase().includes('visit website'))?.href || '';

      const fullText = document.body.innerText;

      // Location pattern e.g. City, ST 12345 (US zip style)
      const locationMatch = fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}/);

      // Principal Contacts line extraction
      const principalMatch = fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i);
      const principalContactRaw = principalMatch?.[1]?.trim() || '';

      // Industry categories extraction, assume next capital letter line after 'Business Categories'
      const industryMatch = fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(t => t.trim()).join(', ') || '';

      return { businessName, principalContact: principalContactRaw, location: locationMatch?.[0] || '', industry, website };
    });

    data.businessName = cleanBusinessName(data.businessName);
    const split = cleanAndSplitName(data.principalContact, data.businessName);

    if (!split || !data.website || !data.businessName) {
      console.log('⚠ Incomplete profile. Skipping.');
      return null;
    }

    return {
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
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    return null;
  }
}

// Add new lead if unique, return true if added
function storeNewLead(record) {
  const url = record['website url'];
  if (!url || allLeads.has(url)) return false;
  allLeads.set(url, record);
  return true;
}

// Save all leads to NDJSON file with pretty formatting and double newlines between records
async function saveAllLeads() {
  const records = Array.from(allLeads.values());
  const ndjson = records.map(obj => JSON.stringify(obj, null, 2)).join('\n\n') + '\n';
  await fsPromises.writeFile(leadsPath, ndjson, 'utf-8');
  console.log(`💾 Saved ${records.length} total leads to ${leadsPath}`);
}

(async () => {
  await fsExtra.ensureDir(path.dirname(leadsPath));
  await loadExistingLeads();

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  for (const baseUrl of SEARCH_URLS) {
    let count = 0;
    let pageNum = 1;

    while (count < 50) {
      const paginatedUrl = `${baseUrl}&page=${pageNum}`;
      console.log(`🌐 Visiting: ${paginatedUrl}`);

      await page.goto(paginatedUrl, { waitUntil: 'networkidle2', timeout: 0 });

      const linksExist = await page.$('a[href*="/profile/"]');
      if (!linksExist) {
        console.log('⚠ No profiles found on this page, stopping pagination.');
        break;
      }

      await humanScroll(page);

      const profileLinks = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href*="/profile/"]'))
          .map(a => a.href)
          .filter((href, i, arr) => !href.includes('/about') && arr.indexOf(href) === i)
      );

      if (profileLinks.length === 0) {
        console.log(`⚠ No profile links on page ${pageNum}.`);
        break;
      }

      let newLeadsThisPage = 0;

      for (const link of profileLinks) {
        if (count >= 50) break;
        const rec = await scrapeProfile(page, link);
        const added = rec && storeNewLead(rec);

        if (rec && added) {
          count++;
          newLeadsThisPage++;
          console.log(`✅ Added: ${rec['business name']}`);
        } else if (rec && !added) {
          console.log(`⏭ Duplicate: ${rec['business name']}`);
        }

        const pause = rec && added ? randomBetween(5000, 12000) : 2000;
        console.log(`⏳ Waiting ${Math.floor(pause / 1000)}s`);
        await delay(pause);
      }

      if (newLeadsThisPage === 0) {
        console.log(`🚫 No eligible leads found on page ${pageNum}. Aborting this block.`);
        break;
      }

      pageNum++;
    }

    console.log(`📌 Finished ${baseUrl} — ${count} new`);
  }

  await browser.close();
  await saveAllLeads();
  console.log('✅ Scraping complete.');
})();
