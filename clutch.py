import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs/promises';
import fsExtra from 'fs-extra';
import path from 'path';

puppeteer.use(StealthPlugin());

const START_URL = 'https://clutch.co/us/law?agency_size=2+-+9&related_services=field_pp_sl_tax_law';
const leadsPath = path.join('leads', 'scraped_leads.ndjson');

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

const allLeads = new Map();

async function loadExistingLeads() {
  if (!await fsExtra.pathExists(leadsPath)) return;
  const content = await fs.readFile(leadsPath, 'utf-8');
  const blocks = content.split(/\n\s*\n/);
  for (const block of blocks) {
    if (!block.trim()) continue;
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

function isValidWebsite(url) {
  return typeof url === 'string' && url.startsWith('http');
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
  await fs.writeFile(leadsPath, ndjson, 'utf-8');
  console.log(`💾 Saved ${records.length} total leads to ${leadsPath}`);
}

async function scrapeProfile(page, profileUrl) {
  try {
    await page.goto(profileUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
    console.log(`🔍 Scraping: ${profileUrl}`);
    await delay(randomBetween(1000, 2500));

    return await page.evaluate(() => {
      const businessName = document.querySelector('h1')?.innerText?.trim() || '';
      const website = document.querySelector('.website-link__item a')?.href || '';
      const location = document.querySelector('.location')?.innerText?.trim() || '';
      const servicesNodes = [...document.querySelectorAll('.service-focus__item')];
      const servicesOffered = servicesNodes.map(n => n.innerText.trim()).join(', ');
      const yearText = document.querySelector('.field--name-field-year-founded')?.innerText || '';
      const founded = yearText.match(/\d{4}/)?.[0] || '';

      return {
        businessName,
        website,
        servicesOffered,
        location,
        founded
      };
    });

  } catch (err) {
    console.error(`❌ Error scraping profile: ${err.message}`);
    return null;
  }
}

async function scrapeDirectory() {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  let pageNum = 0;
  while (true) {
    const pageUrl = `${START_URL}&page=${pageNum}`;
    console.log(`🌐 Visiting: ${pageUrl}`);
    await page.goto(pageUrl, { waitUntil: 'networkidle2', timeout: 0 });

    const profileLinks = await page.evaluate(() =>
      Array.from(document.querySelectorAll('a[href^="/profile/"]'))
        .map(a => a.href)
        .filter((href, i, arr) => arr.indexOf(href) === i)
    );

    if (profileLinks.length === 0) {
      console.log('📭 No more profiles found. Stopping.');
      break;
    }

    let newLeadsThisPage = 0;

    for (const link of profileLinks) {
      const fullLink = `https://clutch.co${link}`;
      const data = await scrapeProfile(page, fullLink);

      if (
        data &&
        isValidWebsite(data.website) &&
        data.founded &&
        parseInt(data.founded) >= 2021 &&
        parseInt(data.founded) <= 2025
      ) {
        const record = {
          'business name': data.businessName,
          'website url': data.website,
          'services offered': data.servicesOffered,
          'location': data.location,
          'founded': data.founded,

          'email': '',
          'web copy': '',
          'email 1': '',
          'email 2': '',
          'email 3': '',
          'initial date': '',
          'follow-up 1 date': '',
          'follow-up 2 date': '',
          'reply': ''
        };

        const added = storeNewLead(record);
        if (added) {
          newLeadsThisPage++;
          console.log(`✅ Added: ${data.businessName}`);
        } else {
          console.log(`⏭ Duplicate: ${data.businessName}`);
        }
      } else {
        console.log(`🚫 Skipped (invalid year or site): ${data?.businessName || '[no name]'}`);
      }

      const pause = randomBetween(2000, 4000);
      console.log(`⏳ Waiting ${Math.floor(pause / 1000)}s`);
      await delay(pause);
    }

    if (newLeadsThisPage === 0) break;
    pageNum++;
  }

  await browser.close();
}

(async () => {
  await fsExtra.ensureDir(path.dirname(leadsPath));
  await loadExistingLeads();
  await scrapeDirectory();
  await saveAllLeads();
  console.log('✅ Scraping complete.');
})();
