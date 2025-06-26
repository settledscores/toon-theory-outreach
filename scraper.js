import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();
puppeteer.use(StealthPlugin());

const NICHES = [
  'https://www.bbb.org/us/fl/alafaya/category/business-consultant?page=1'
];

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

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;

  // Remove honorifics and punctuation at ends
  const honorifics = ['Mr\\.', 'Mrs\\.', 'Ms\\.', 'Miss', 'Dr\\.', 'Prof\\.', 'Mx\\.'];
  const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');
  let clean = raw.replace(honorificRegex, '').replace(/[,/\\]+$/, '').trim();

  // If comma exists, split name/title
  let namePart = clean;
  let titlePart = '';
  if (clean.includes(',')) {
    const [name, title] = clean.split(',', 2);
    namePart = name.trim();
    titlePart = title.trim();
  }

  // Reject reused business name
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;

  // Split name by spaces (keep initials with dots)
  const tokens = namePart.split(/\s+/).filter(Boolean);
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
    await delay(randomBetween(1500, 3000));
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

    const split = cleanAndSplitName(data.principalContact, data.businessName);
    if (!split || !data.website || !data.businessName) return null;

    return {
      ...data,
      ...split
    };

  } catch (err) {
    console.error(`❌ Failed to extract: ${url} — ${err.message}`);
    return null;
  }
}

async function syncToAirtable(record) {
  if (
    !process.env.AIRTABLE_API_KEY ||
    !process.env.AIRTABLE_BASE_ID ||
    !process.env.SCRAPER_TABLE_NAME
  ) {
    console.error('❌ Airtable config missing.');
    return;
  }

  const body = {
    fields: {
      'business name': record.businessName,
      'website url': record.website,
      'location': record.location,
      'industry': record.industry,
      'years': record.years,
      'First Name': record.firstName,
      'Middle Name': record.middleName,
      'Last Name': record.lastName,
      'Decision Maker Title': record.title
    }
  };

  try {
    const res = await fetch(`https://api.airtable.com/v0/${process.env.AIRTABLE_BASE_ID}/${process.env.SCRAPER_TABLE_NAME}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.AIRTABLE_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    const result = await res.text();

    if (!res.ok) {
      console.error(`❌ Airtable error (${res.status}): ${result}`);
    } else {
      console.log(`✅ Scraped: ${record.businessName}`);
    }
  } catch (err) {
    console.error(`❌ Airtable request failed: ${err.message}`);
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

  for (const baseUrl of NICHES) {
    console.log(`🔍 Scraping niche: ${baseUrl}`);
    let pageNum = 1;
    let validCount = 0;
    let consecutiveEmpty = 0;

    while (validCount < 50 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1500, 3000));
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
          const dedupKey = `${profile.businessName}|${profile.website}`;
          if (!seen.has(dedupKey)) {
            seen.add(dedupKey);
            await syncToAirtable(profile);
            validCount++;
            scrapedThisPage++;
          }
        }

        await delay(randomBetween(5000, 10000));
        if (validCount >= 50) break;
      }

      consecutiveEmpty = scrapedThisPage === 0 ? consecutiveEmpty + 1 : 0;
      pageNum++;
    }

    console.log(`🏁 Finished: ${baseUrl} — ${validCount} saved`);
  }

  await browser.close();
  console.log('✅ All niches done.');
})();
