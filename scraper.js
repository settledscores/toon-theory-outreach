import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import fs from 'fs';
import dotenv from 'dotenv';

dotenv.config();
puppeteer.use(StealthPlugin());

const NICHES = [
  'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Austin%2C+TX&find_country=USA',
  'https://www.bbb.org/search?find_country=USA&find_entity=60170-110&find_id=6349_000-000-7524&find_latlng=28.511388%2C-81.308452&find_loc=Orlando%2C%20FL&find_text=Business%20Development&find_type=Category&page=1',
  'https://www.bbb.org/search?find_text=Financial+Consultants&find_entity=55683-000&find_type=Category&find_loc=San+Jose%2C+CA&find_country=USA',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Brooklyn%2C+NY&find_country=USA',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=San+Francisco%2C+CA&find_country=USA',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Austin%2C+TX&find_country=USA',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Indianapolis%2C+IN&find_country=USA',
  'https://www.bbb.org/search?find_text=Management+Consultant&find_entity=60533-000&find_type=Category&find_loc=Orlando%2C+FL&find_country=USA',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=60509-000&find_type=Category&find_loc=Orlando%2C+FL&find_country=USA',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=&find_type=&find_loc=San+Diego%2C+CA&find_country=USA',
  'https://www.bbb.org/search?find_text=Management+Consultant&find_entity=60533-000&find_type=Category&find_loc=San+Diego%2C+CA&find_country=USA',
  'https://www.bbb.org/search?find_text=Management+Consultant&find_entity=&find_type=&find_loc=Detroit%2C+MI&find_country=USA'
];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  const scrolls = randomBetween(3, 6);
  for (let i = 0; i < scrolls; i++) {
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(300, 700));
    await page.mouse.move(randomBetween(200, 1000), randomBetween(100, 800));
  }
}

async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 0 });
    await delay(randomBetween(2000, 4000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = Array.from(document.querySelectorAll('script')).find(s => s.textContent.includes('business_name'));
      const businessName = scriptTag?.textContent.match(/"business_name":"([^"]+)"/)?.[1] || '';
      const website = Array.from(document.querySelectorAll('a')).find(a => a.innerText.toLowerCase().includes('visit website'))?.href || '';
      const addressMatch = document.body.innerText.match(/\s[A-Z]{2}\s\d{5}(-\d{4})?/);
      const location = addressMatch?.[0]?.trim() || '';
      const mgmt = document.body.innerText.match(/Business Management:\s*(Mr\.|Ms\.|Mrs\.|Dr\.)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),?\s*(.*)/);
      const principalContact = mgmt?.[2]?.trim() || '';
      const jobTitle = mgmt?.[3]?.trim().split('\n')[0] || '';
      const years = document.body.innerText.match(/Business Started:\s*(.+)/)?.[1]?.trim() || '';
      const industryMatch = document.body.innerText.match(/Business Categories\s+([\s\S]*?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(s => s.trim()).filter(Boolean).join(', ') || '';
      return { businessName, principalContact, jobTitle, location, years, industry, website };
    });

    if (!data.website || !data.principalContact) return null;
    return data;
  } catch (e) {
    console.warn('⚠️ Failed to scrape:', url);
    return null;
  }
}

async function syncToAirtable(record) {
  if (!process.env.AIRTABLE_API_KEY) return;
  const body = {
    fields: {
      'business name': record.businessName,
      'website url': record.website,
      'notes': '',
      'location': record.location,
      'industry': record.industry,
      'years': record.years,
      'Decision Maker Name': record.principalContact,
      'Decision Maker Title': record.jobTitle
    }
  };
  await fetch(`https://api.airtable.com/v0/${process.env.AIRTABLE_BASE_ID}/${process.env.SCRAPER_TABLE_NAME}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.AIRTABLE_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const visited = new Set();

  for (const nicheUrl of NICHES) {
    console.log(`🔎 Starting niche: ${nicheUrl}`);
    let collected = 0;
    let pageNum = 1;

    while (collected < 50) {
      const pagedUrl = `${nicheUrl}${nicheUrl.includes('page=') ? '' : `&page=${pageNum}`}`;
      console.log(`📄 Page ${pageNum}: ${pagedUrl}`);

      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 3000));
      await humanScroll(page);

      const profileLinks = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href*="/profile/"]'))
          .map(a => a.href)
          .filter((v, i, arr) => arr.indexOf(v) === i && !v.includes('/about'))
      );

      if (!profileLinks.length) break;

      for (const link of profileLinks) {
        if (visited.has(link) || collected >= 50) continue;
        visited.add(link);
        console.log(`🔗 Visiting ${link}`);

        const data = await extractProfile(page, link);
        if (data) {
          console.table(data);
          await syncToAirtable(data);
          collected++;
        }

        await delay(randomBetween(7000, 25000));
      }

      pageNum++;
    }

    console.log(`✅ Finished niche with ${collected} profiles.`);
  }

  await browser.close();
  console.log('🏁 All done.');
})();
