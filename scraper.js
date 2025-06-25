const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

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
    console.log(`🧭 Scraping profile: ${url}`);
    await delay(randomBetween(2000, 4000));
    await humanScroll(page);

    const timestamp = Date.now();
    await page.screenshot({ path: `bbb_screenshot_${timestamp}.png`, fullPage: true });
    fs.writeFileSync(`bbb_html_${timestamp}.html`, await page.content());

    const data = await page.evaluate(() => {
      const safeText = el => el?.innerText?.trim() || '';
      const businessName = document.querySelector('h1')?.innerText.trim() || '';

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
  } catch (err) {
    console.error(`❌ Error scraping ${url}:`, err.message);
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
  await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 0 });
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

  for (let i = 0; i < 1 && i < profileLinks.length; i++) {
    const link = profileLinks[i];
    console.log(`🔗 Visiting ${link}`);
    await scrapeProfile(page, link);

    const waitTime = randomBetween(15000, 60000);
    console.log(`⏳ Waiting ${Math.round(waitTime / 1000)}s before next.`);
    await delay(waitTime);
  }

  await browser.close();
  console.log('✅ Scrape complete.');
})();
