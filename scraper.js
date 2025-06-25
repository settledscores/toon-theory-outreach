import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fetch from 'node-fetch';
import dotenv from 'dotenv';
import fs from 'fs';

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
  const steps = randomBetween(5, 10);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
    await page.evaluate(() => {
      window.scrollBy(0, window.innerHeight / 2);
    });
    await delay(randomBetween(300, 1000));
  }
  await page.mouse.move(randomBetween(200, 800), randomBetween(100, 600));
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

      const addressMatch = document.body.innerText.match(/(?:[A-Z][a-z]+,)?\s?[A-Z]{2}\s\d{5}(-\d{4})?/);
      const location = addressMatch?.[0]?.trim() || '';

      const mgmtMatch = document.body.innerText.match(/Business Management:\s*(Mr\.|Ms\.|Mrs\.|Dr\.)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),?\s*(Owner|CEO|Manager|President|Founder)?/i);
      const principalContact = mgmtMatch?.[2]?.trim() || '';
      const jobTitle = mgmtMatch?.[3]?.trim() || '';

      const yearsMatch = document.body.innerText.match(/Business Started:\s*(.+)/i);
      const years = yearsMatch?.[1]?.trim().split('\n')[0] || '';

      const industryMatch = document.body.innerText.match(/Business Categories\s+([\s\S]*?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(s => s.trim()).filter(Boolean).join(', ') || '';

      return {
        businessName,
        principalContact,
        jobTitle,
        location,
        years,
        industry,
        website
      };
    });

    if (!data.website || !data.principalContact || !data.businessName) return null;
    return data;

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
  ) return;

  const body = {
    fields: {
      'business name': record.businessName,
      'website url': record.website,
      'location': record.location,
      'industry': record.industry,
      'years': record.years,
      'Decision Maker Name': record.principalContact,
      'Decision Maker Title': record.jobTitle
    }
  };

  const res = await fetch(`https://api.airtable.com/v0/${process.env.AIRTABLE_BASE_ID}/${process.env.SCRAPER_TABLE_NAME}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.AIRTABLE_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const text = await res.text();
    console.error(`❌ Airtable sync failed (${res.status}):`, text);
  } else {
    console.log(`✅ Scraped: ${record.businessName}`);
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

  const visited = new Set();

  for (const niche of NICHES) {
    console.log(`🔍 Starting niche: ${niche}`);
    let pageNum = 1;
    let totalScraped = 0;

    while (totalScraped < 50) {
      const pagedUrl = `${niche}&page=${pageNum}`;
      console.log(`📄 Scraping page ${pageNum}`);
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 3000));
      await humanScroll(page);

      const links = await page.evaluate(() =>
        [...document.querySelectorAll('a[href*="/profile/"]')]
          .map(a => a.href)
          .filter((href, i, arr) => href.includes('/profile/') && arr.indexOf(href) === i)
      );

      if (links.length === 0) break;

      for (const link of links) {
        if (visited.has(link)) continue;
        visited.add(link);

        console.log(`🔗 Visiting: ${link}`);
        const data = await extractProfile(page, link);

        if (data) {
          await syncToAirtable(data);
          totalScraped++;
        }

        await delay(randomBetween(7000, 25000));
        if (totalScraped >= 50) break;
      }

      pageNum++;
    }

    console.log(`🏁 Finished niche: ${niche} — Scraped ${totalScraped} valid profiles`);
  }

  await browser.close();
  console.log('✅ All niches complete.');
})();
