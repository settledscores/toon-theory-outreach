import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import fsPromises from 'fs/promises';
import fsExtra from 'fs-extra';
import path from 'path';

puppeteer.use(StealthPlugin());

const SEARCH_URLS = [
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=60451-000&find_type=Category&find_loc=Seattle%2C+WA&find_country=USA',
  'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Seattle%2C+WA&find_country=USA',
  'https://www.bbb.org/search?find_text=Business+Consultants&find_entity=60172-000&find_type=Category&find_loc=Seattle%2C+WA&find_country=USA',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=60509-000&find_type=Category&find_loc=Seattle%2C+WA&find_country=USA',
  'https://www.bbb.org/search?find_text=tax+consulting&find_entity=60858-000&find_type=Category&find_loc=Seattle%2C+WA&find_country=USA'
];

const leadsPath = path.join('leads', 'scraped_leads.ndjson');
const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|esquire|cpa|mba|jd|j\.d\.|phd|m\.d\.|md|cfa|cfe|cma|cfp|llb|ll\.b\.|llm|ll\.m\.|rn|np|pa|pmp|pe|p\.eng|cis|cissp|aia|shrm[-\s]?(cp|scp)|phr|sphr|gphr|ra|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|pcc|acc|mcc|six\s?sigma|ceo|cto|cmo|chro|ret\.?|gen\.?|col\.?|maj\.?|capt?\.?|lt\.?|usa|usaf|usmc|usn|uscg|comp?tia|aws|hon|rev|fr|rabbi|imam|president|founder)\b\.?/gi];

const allLeads = new Map();

async function loadExistingLeads() {
  if (!fs.existsSync(leadsPath)) return;
  const content = await fsPromises.readFile(leadsPath, 'utf-8');
  const blocks = content.split(/\n\s*\n/);
  for (const block of blocks) {
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

function cleanBusinessName(name) {
  if (!name) return '';
  let cleaned = name;
  for (const suffix of businessSuffixes) cleaned = cleaned.replace(suffix, '').trim();
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
  if (tokens.length < 2 || tokens.length > 4) return null;
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

async function humanScroll(page) {
  const steps = randomBetween(5, 8);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(150, 500));
  }
}

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
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    return null;
  }
}

function storeNewLead(record) {
  const url = record['website url'];
  if (!url || allLeads.has(url)) return false;
  allLeads.set(url, record);
  return true;
}

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
