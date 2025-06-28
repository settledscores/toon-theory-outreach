import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs/promises';
import path from 'path';
import fsExtra from 'fs-extra';

puppeteer.use(StealthPlugin());

const BASE_URL = 'https://www.bbb.org/search?find_text=Accounting&find_entity=&find_type=Category&find_loc=Austin%2C+TX&find_country=USA';
const scrapedFilePath = path.join('leads', 'scraped_leads.json');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  const steps = randomBetween(4, 8);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(0, 800), randomBetween(0, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
    await delay(randomBetween(500, 1500));
  }
}

async function scrapeProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 0 });
    console.log(`🧭 Scraping profile: ${url}`);
    await delay(randomBetween(2000, 4000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const safeText = el => el?.innerText?.trim() || '';

      const scriptTag = Array.from(document.querySelectorAll('script'))
        .find(s => s.textContent.includes('"business_name"'));
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

    console.log('📋 Scraped Data:');
    console.table(data);
    return data;

  } catch (err) {
    console.error(`❌ Error scraping ${url}:`, err.message);
    return null;
  }
}

async function updateLeadsJson(newData) {
  let existing = { scraped_at: '', total: 0, records: [] };

  if (await fsExtra.pathExists(scrapedFilePath)) {
    const raw = await fs.readFile(scrapedFilePath, 'utf-8');
    existing = JSON.parse(raw);
  }

  const dedupeKey = `${newData.businessName}|${newData.website}`;
  const map = new Map(
    existing.records.map(r => [`${r["business name"]}|${r["website url"]}`, r])
  );

  map.set(dedupeKey, {
    "business name": newData.businessName,
    "website url": newData.website,
    "location": newData.location,
    "industry": newData.industry,
    "years": newData.years,
    "Decision Maker Name": newData.principalContact,
    "Decision Maker Title": newData.jobTitle
  });

  const final = Array.from(map.values());

  await fs.writeFile(scrapedFilePath, JSON.stringify({
    scraped_at: new Date().toISOString(),
    total: final.length,
    records: final
  }, null, 2));

  console.log(`✅ Updated ${scrapedFilePath} with ${final.length} total records`);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  console.log('🔍 Visiting search page...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 0 });
  await page.waitForSelector('a[href*="/profile/"]');
  await humanScroll(page);

  const profileLinks = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href*="/profile/"]'))
      .map(a => a.href)
      .filter((href, i, arr) => !href.includes('/about') && arr.indexOf(href) === i)
  );

  console.log(`🔗 Found ${profileLinks.length} profile links.`);

  for (let i = 0; i < 3 && i < profileLinks.length; i++) {
    const link = profileLinks[i];
    const data = await scrapeProfile(page, link);
    if (data) await updateLeadsJson(data);

    const wait = randomBetween(15000, 30000);
    console.log(`⏳ Waiting ${Math.floor(wait / 1000)}s...`);
    await delay(wait);
  }

  await browser.close();
  console.log('✅ Scraping complete.');
})();
