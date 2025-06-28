import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs/promises';
import path from 'path';
import { execSync } from 'child_process';

puppeteer.use(StealthPlugin());

const NICHES = [
  "https://www.bbb.org/search?find_text=Human+Resources&find_entity=&find_type=&find_loc=Boston%2C+MA&find_country=USA"
];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

const businessSuffixes = [/\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i];
const nameSuffixes = [/\b(jr|sr|i{1,3}|iv|v|esq|cpa|mba|phd|md|ceo|cto|cmo|founder|president)\b/gi];

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
  if (clean.includes(',')) [namePart, titlePart] = clean.split(',', 2).map(s => s.trim());
  if (namePart.toLowerCase() === businessName.toLowerCase()) return null;
  let tokens = namePart.split(/\s+/).filter(Boolean);
  if (tokens.length > 2 && nameSuffixes.some(r => r.test(tokens[tokens.length - 1]))) tokens.pop();
  if (tokens.length < 2 || tokens.length > 4) return null;
  return {
    firstName: tokens[0],
    middleName: tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    lastName: tokens[tokens.length - 1],
    title: titlePart
  };
}

async function extractProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 0 });
    await delay(randomBetween(1500, 3000));
    await humanScroll(page);

    const data = await page.evaluate(() => {
      const scriptTag = [...document.querySelectorAll('script')].find(s => s.textContent.includes('business_name'));
      const businessNameMatch = scriptTag?.textContent.match(/"business_name"\s*:\s*"([^"]+)"/);
      const businessName = businessNameMatch?.[1] || '';
      const website = [...document.querySelectorAll('a')].find(a => a.textContent.toLowerCase().includes('visit website'))?.href || '';
      const fullText = document.body.innerText;
      const location = fullText.match(/\b[A-Z][a-z]+,\s[A-Z]{2}\s\d{5}/)?.[0] || '';
      const principal = fullText.match(/Principal Contacts\s+(.*?)(\n|$)/i)?.[1]?.trim() || '';
      const industryMatch = fullText.match(/Business Categories\s+([\s\S]+?)\n[A-Z]/i);
      const industry = industryMatch?.[1]?.split('\n').map(t => t.trim()).join(', ') || '';
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
    console.error(`❌ Failed on ${url} — ${err.message}`);
    return null;
  }
}

async function saveAndCommit(records) {
  const filePath = path.join('leads', 'scraped_leads.json');
  await fs.mkdir('leads', { recursive: true });

  const previous = await fs.readFile(filePath, 'utf8').catch(() => '[]');
  const previousData = JSON.parse(previous);
  const newRecords = [...previousData, ...records];

  await fs.writeFile(filePath, JSON.stringify(newRecords, null, 2));
  console.log(`✅ Saved ${records.length} new leads.`);

  execSync(`git config user.name "github-actions"`);
  execSync(`git config user.email "github-actions@github.com"`);
  execSync(`git add ${filePath}`);
  execSync(`git commit -m "⬆️ Update scraped leads [${new Date().toISOString()}]" || echo "No changes to commit."`);
  execSync(`git push`);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const seen = new Set(), deduped = new Set(), records = [];

  for (const baseUrl of NICHES) {
    let pageNum = 1, validCount = 0, consecutiveEmpty = 0;
    while (validCount < 3 && consecutiveEmpty < 5) {
      const pagedUrl = baseUrl.includes('page=') ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      await page.goto(pagedUrl, { waitUntil: 'domcontentloaded', timeout: 0 });
      await delay(randomBetween(1000, 2000));
      await humanScroll(page);
      const links = await page.evaluate(() => [...document.querySelectorAll('a[href*="/profile/"]')].map(a => a.href));
      if (!links.length) break;

      let scraped = 0;
      for (const link of links) {
        if (seen.has(link)) continue;
        seen.add(link);
        const profile = await extractProfile(page, link);
        if (profile) {
          const key = `${profile["business name"].toLowerCase()}|${profile["website url"].toLowerCase()}`;
          if (!deduped.has(key)) {
            deduped.add(key);
            records.push(profile);
            console.log('📦', profile);
            validCount++;
            scraped++;
          }
        }
        await delay(randomBetween(3000, 6000));
        if (validCount >= 3) break;
      }
      consecutiveEmpty = scraped === 0 ? consecutiveEmpty + 1 : 0;
      pageNum++;
    }
    console.log(`🏁 Done with: ${baseUrl} — ${validCount} saved`);
  }

  await browser.close();
  await saveAndCommit(records);
})();
