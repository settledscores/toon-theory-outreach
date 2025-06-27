import puppeteer from 'puppeteer';
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();
puppeteerExtra.use(StealthPlugin());

const NICHES = [
  "https://www.bbb.org/search?find_text=Legal+Services&find_loc=San+Diego%2C+CA",
  "https://www.bbb.org/search?find_text=Management+Consultant&find_loc=San+Diego%2C+CA",
  "https://www.bbb.org/search?find_text=Management+Consultant&find_loc=Detroit%2C+MI",
  "https://www.bbb.org/search?find_text=Staffing+Agencies&find_loc=Washington%2C+PA",
  "https://www.bbb.org/search?find_text=Human+Resources&find_loc=Boston%2C+MA"
];

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|esquire|cpa|mba|jd|j\.d\.|phd|m\.d\.|md|cfa|cfe|cma|cfp|llb|ll\.b\.|llm|ll\.m\.|rn|np|pa|pmp|pe|p\.eng|cis|cissp|aia|shrm[-\s]?(cp|scp)|phr|sphr|gphr|ra|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|pcc|acc|mcc|six\s?sigma|ceo|cto|cmo|chro|ret\.?|gen\.?|col\.?|maj\.?|capt?\.?|lt\.?|usa|usaf|usmc|usn|uscg|comp?tia|aws|hon|rev|fr|rabbi|imam|president|founder)\b\.?/gi];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  const steps = randomBetween(4, 6);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(200, 500));
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
  const lowerRaw = raw.toLowerCase();
  if (lowerRaw.includes('support') || lowerRaw.includes('customer') || lowerRaw.length < 4) return null;

  const honorifics = ['Mr.', 'Mrs.', 'Ms.', 'Miss', 'Dr.', 'Prof.', 'Mx.'];
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
  tokens = tokens.filter(token => !nameSuffixes.some(regex => regex.test(token)));

  if (tokens.length < 2 || tokens.length > 4) return null;

  const firstName = tokens[0];
  const lastName = tokens[tokens.length - 1];
  const middleName = tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '';

  return {
    firstName,
    middleName,
    lastName,
    title: titlePart
  };
}

async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(1200, 2000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = [...document.querySelectorAll('script')].find(s => s.textContent.includes('"business_name"'));
      const businessNameMatch = scriptTag?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/);
      const businessName = businessNameMatch?.[1] || '';

      const website = Array.from(document.querySelectorAll('a')).find(a =>
        a.innerText.toLowerCase().includes('visit website') && a.href.includes('http')
      )?.href || '';

      const fullText = document.body.innerText;

      const locationMatch = fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}(-\d{4})?/);
      const location = locationMatch?.[0] || '';

      const principalMatch = fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i);
      const principalContactRaw = principalMatch?.[1]?.trim() || '';

      const yearsMatch = fullText.match(/Business Started:\s*(.+)/i);
      const years = yearsMatch?.[1]?.split('\n')[0].trim() || '';

      const industryMatch = fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(t => t.trim()).join(', ') || '';

      return {
        businessName,
        principalContact: principalContactRaw,
        location,
        years,
        industry,
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

async function syncToNocoDB(record) {
  const apiKey = process.env.NOCODB_API_KEY;
  const baseUrl = process.env.NOCODB_BASE_URL;
  const projectId = process.env.NOCODB_PROJECT_ID;
  const tableId = process.env.NOCODB_SCRAPER_TABLE_ID;

  if (!apiKey || !baseUrl || !projectId || !tableId) {
    console.error('❌ Missing NocoDB config.');
    return;
  }

  const url = `${baseUrl}/api/v1/db/data/${projectId}/${tableId}`;
  const body = {
    "business name": record.businessName,
    "website url": record.website,
    "location": record.location,
    "industry": record.industry,
    "years": record.years,
    "First Name": record.firstName,
    "Middle Name": record.middleName,
    "Last Name": record.lastName,
    "Decision Maker Title": record.title,
    "Profile Link": record.profileLink
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'xc-token': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    const result = await res.text();

    if (!res.ok) {
      console.error(`❌ NocoDB error (${res.status}): ${result}`);
    } else {
      console.log(`✅ Synced: ${record.businessName}`);
    }
  } catch (err) {
    console.error(`❌ NocoDB sync failed: ${err.message}`);
  }
}

(async () => {
  const browser = await puppeteerExtra.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const seen = new Set();
  const deduped = new Set();

  for (const baseUrl of NICHES) {
    console.log(`🔍 Scraping niche: ${baseUrl}`);
    let pageNum = 1;
    let validCount = 0;
    let consecutiveEmpty = 0;

    while (validCount < 20 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);

      const links = await page.evaluate(() => {
        return [...document.querySelectorAll('a[href*="/profile/"]')]
          .map(a => a.href)
          .filter((href, i, arr) => arr.indexOf(href) === i);
      });

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
