import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';

puppeteer.use(StealthPlugin());

const NICHES = [
  "https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Boston%2C+MA&find_country=USA"
];

const SEATABLE_API_KEY = 'c2beb2333e140b5698cbe5e5031aa3b0743e7013';
const SEATABLE_BASE_URL = 'https://cloud.seatable.io';
const SEATABLE_DTABLE_UUID = 'd603f65e-b769-448c-b7c8-4f155c3f38b0';
const SEATABLE_SCRAPER_TABLE_NAME = 'Scraper Leads';

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|esquire|cpa|mba|jd|j\.d\.|phd|m\.d\.|md|cfa|cfe|cma|cfp|llb|ll\.b\.|llm|ll\.m\.|rn|np|pa|pmp|pe|p\.eng|cis|cissp|aia|shrm[-\s]?(cp|scp)|phr|sphr|gphr|ra|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|pcc|acc|mcc|six\s?sigma|ceo|cto|cmo|chro|ret\.?|gen\.?|col\.?|maj\.?|capt?\.?|lt\.?|usa|usaf|usmc|usn|uscg|comp?tia|aws|hon|rev|fr|rabbi|imam|president|founder)\b\.?/gi];

const delay = ms => new Promise(res => setTimeout(res, ms));
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
  for (const suffix of businessSuffixes) {
    name = name.replace(suffix, '').trim();
  }
  return name.replace(/[.,]$/, '').trim();
}

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;
  const honorifics = ['Mr\\.', 'Mrs\\.', 'Ms\\.', 'Miss', 'Dr\\.', 'Prof\\.', 'Mx\\.'];
  const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');
  let clean = raw.replace(honorificRegex, '').replace(/[,/\\]+$/, '').trim();
  let namePart = clean, titlePart = '';
  if (clean.includes(',')) {
    const [name, title] = clean.split(',', 2);
    namePart = name.trim();
    titlePart = title.trim();
  }
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;
  let tokens = namePart.split(/\s+/).filter(Boolean);
  if (tokens.length > 2 && nameSuffixes.some(r => r.test(tokens[tokens.length - 1]))) tokens.pop();
  if (tokens.length < 2 || tokens.length > 4) return null;
  const firstName = tokens[0];
  const lastName = tokens[tokens.length - 1];
  const middleName = tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '';
  return { firstName, middleName, lastName, title: titlePart };
}

async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(1500, 3000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const script = [...document.querySelectorAll('script')].find(s => s.textContent.includes('"business_name"'));
      const businessName = script?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/)?.[1] || '';
      const website = [...document.querySelectorAll('a')].find(a => a.innerText.toLowerCase().includes('visit website') && a.href.includes('http'))?.href || '';
      const fullText = document.body.innerText;
      const location = fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}(-\d{4})?/)?.[0] || '';
      const principal = fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i)?.[1]?.trim() || '';
      const industry = fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i)?.[1]?.split('\n').map(t => t.trim()).join(', ') || '';
      return { businessName, principalContact: principal, location, industry, website };
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
  const url = `${SEATABLE_BASE_URL}/api/v2/dtable-db/dtables/${SEATABLE_DTABLE_UUID}/tables/${encodeURIComponent(SEATABLE_SCRAPER_TABLE_NAME)}/records/batch/`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${SEATABLE_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ records })
    });

    const result = await res.json();
    if (!res.ok) {
      console.error(`❌ SeaTable error (${res.status}): ${JSON.stringify(result)}`);
    } else {
      console.log(`✅ Synced ${records.length} records to SeaTable`);
    }
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

  for (const baseUrl of NICHES) {
    console.log(`🔍 Scraping niche: ${baseUrl}`);
    let pageNum = 1;
    let validCount = 0;
    let consecutiveEmpty = 0;

    while (validCount < 3 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);

      const links = await page.evaluate(() =>
        [...document.querySelectorAll('a[href*="/profile/"]')]
          .map(a => a.href)
          .filter((href, i, arr) => arr.indexOf(href) === i)
      );

      if (!links.length) break;

      let scrapedThisPage = 0;
      for (const link of links) {
        if (seen.has(link)) continue;
        seen.add(link);

        const profile = await extractProfile(page, link);
        if (profile) {
          const dedupKey = `${profile["business name"].toLowerCase()}|${profile["website url"].toLowerCase()}`;
          if (!deduped.has(dedupKey)) {
            deduped.add(dedupKey);
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
