// scraper.js

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

const BASE_URL = 'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Austin%2C+TX&find_country=USA';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

async function humanScroll(page) {
  const scrollSteps = randomBetween(4, 8);
  for (let i = 0; i < scrollSteps; i++) {
    await page.mouse.move(randomBetween(0, 800), randomBetween(0, 600));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight / 3));
    await delay(randomBetween(500, 1500));
  }
}

async function scrapeProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(2000, 5000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const getText = sel => document.querySelector(sel)?.innerText?.trim() || '';
      const businessName = getText('h1');
      const principalContact = getText('[data-testid="leadership-name"]');
      const jobTitle = getText('[data-testid="leadership-title"]');
      const location = getText('[data-testid="business-address"]');
      const years = getText('[data-testid="years-in-business"]');
      const industry = getText('[data-testid="business-category"]');
      const website = document.querySelector('a[data-testid="business-website"]')?.href || '';
      return { businessName, principalContact, jobTitle, location, years, industry, website };
    });

    return data;
  } catch (err) {
    console.error(`❌ Failed to scrape ${url}:`, err.message);
    return null;
  }
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium-browser',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  console.log('🔍 Navigating to BBB search page...');
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await delay(randomBetween(2000, 4000));
  await humanScroll(page);

  const profileLinks = await page.evaluate(() => {
    return [...document.querySelectorAll('[data-testid="business-title"] > a')]
      .map(a => a.href)
      .filter((v, i, arr) => arr.indexOf(v) === i);
  });

  console.log(`✅ Found ${profileLinks.length} profiles.`);

  const results = [];
  for (let i = 0; i < Math.min(profileLinks.length, 5); i++) {
    const link = profileLinks[i];
    console.log(`🔗 Visiting ${link}`);
    const profile = await scrapeProfile(page, link);
    if (profile) results.push(profile);

    const waitTime = randomBetween(15000, 60000);
    console.log(`⏳ Waiting ${Math.round(waitTime / 1000)}s to mimic human behavior.`);
    await delay(waitTime);
  }

  await browser.close();
  fs.writeFileSync('bbb_results.json', JSON.stringify(results, null, 2));
  console.log('📄 Results saved to bbb_results.json');
})();
