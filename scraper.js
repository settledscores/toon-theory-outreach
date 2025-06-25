const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

const BASE_URL = 'https://www.bbb.org/search?find_text=Accounting&find_entity=60005-101&find_type=Category&find_loc=Austin%2C+TX&find_country=USA';

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
    console.log(`🧭 Currently scraping: ${page.url()}`);

    await delay(randomBetween(2000, 4000));
    await humanScroll(page);

    // Capture screenshot and HTML snapshot
    const timestamp = Date.now();
    const screenshotPath = `bbb_screenshot_${timestamp}.png`;
    const htmlPath = `bbb_html_${timestamp}.html`;

    await page.screenshot({ path: screenshotPath, fullPage: true });
    fs.writeFileSync(htmlPath, await page.content());

    const data = await page.evaluate(() => {
      const getText = sel => document.querySelector(sel)?.innerText?.trim() || '';

      const businessName = getText('[data-testid="business-name"]') ||
        document.querySelector('h1')?.textContent.trim() || '';

      const principalContact = getText('[data-testid="leadership-name"]') ||
        getText('[data-testid="leadership-contact"]');

      const jobTitle = getText('[data-testid="leadership-title"]');
      const location = getText('[data-testid="business-address"]') ||
        getText('[itemprop="address"]');
      const years = getText('[data-testid="years-in-business"]') ||
        getText('[itemprop="foundingDate"]');
      const industry = getText('[data-testid="business-category"]');

      const website = Array.from(document.querySelectorAll('a')).find(a =>
        a.href.includes('http') && /website/i.test(a.innerText)
      )?.href || '';

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

    return data;
  } catch (err) {
    console.error(`❌ Failed to scrape ${url}:`, err.message);
    return null;
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

  console.log('🔍 Navigating to BBB search page...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle2' });
  await page.waitForSelector('a[href*="/profile/"]', { timeout: 15000 });
  await humanScroll(page);

  const profileLinks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('a[href*="/profile/"]'))
      .map(a => a.href)
      .filter((href, i, arr) =>
        href.includes('/profile/') &&
        !href.includes('/about') &&
        arr.indexOf(href) === i
      );
  });

  console.log(`✅ Found ${profileLinks.length} valid profile links.`);

  const results = [];

  for (let i = 0; i < 1 && i < profileLinks.length; i++) {
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
