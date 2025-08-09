// scraper.js
// Full rewrite of your BBB scraper with robust timeouts, retries, and safer parsing.

import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import fsPromises from 'fs/promises';
import fsExtra from 'fs-extra';
import path from 'path';

puppeteer.use(StealthPlugin());

/* ---------------------------
   CONFIG
   --------------------------- */
const leadsPath = path.join('leads', 'scraped_leads.ndjson');
const CHROME_EXECUTABLE = process.env.CHROME_PATH || '/usr/bin/chromium-browser';

// Put Business Consultants (Newark) first as requested
const SEARCH_URLS = [
  // Business Consultants Newark first
  'https://www.bbb.org/search?find_text=Business+Consultants&find_entity=60172-000&find_type=Category&find_loc=Newark%2C+NJ&find_country=USA',

  // New Jerusalem, PA block
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=60451-000&find_type=Category&find_loc=New+Jerusalem%2C+PA&find_country=USA',
  'https://www.bbb.org/search?find_text=Accountant&find_entity=60005-000&find_type=Category&find_loc=New+Jerusalem%2C+PA&find_country=USA',
  'https://www.bbb.org/search?find_text=Business+Consultants&find_entity=60172-000&find_type=Category&find_loc=New+Jerusalem%2C+PA&find_country=USA',
  'https://www.bbb.org/search?find_text=Tax+Consultant&find_entity=60858-000&find_type=Category&find_loc=New+Jerusalem%2C+PA&find_country=USA',
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=60509-000&find_type=Category&find_loc=New+Jerusalem%2C+PA&find_country=USA',

  // Newark remainder
  'https://www.bbb.org/search?find_text=Legal+Services&find_entity=&find_type=&find_loc=Newark%2C+NJ&find_country=USA',
  'https://www.bbb.org/search?find_text=Accountant&find_entity=60005-000&find_type=Category&find_loc=Newark%2C+NJ&find_country=USA',
  'https://www.bbb.org/search?find_text=Tax+Consultant&find_entity=60858-000&find_type=Category&find_loc=Newark%2C+NJ&find_country=USA',
  'https://www.bbb.org/search?find_text=Human+Resources&find_entity=60451-000&find_type=Category&find_loc=Newark%2C+NJ&find_country=USA',
];

const delay = ms => new Promise(res => setTimeout(res, ms));
const randomBetween = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

/* ---------------------------
   CLEANING / PARSING HELPERS
   --------------------------- */

// business suffixes (regexes) to strip
const businessSuffixes = [
  /\b(inc|llc|ltd|corp|co|company|pllc|pc|pa|incorporated|limited|llp|plc)\.?$/i
];

// honorifics and name suffixes (kept similar to your previous list)
const honorifics = ['Mr\\.', 'Mrs\\.', 'Ms\\.', 'Miss', 'Dr\\.', 'Prof\\.', 'Mx\\.'];
const honorificRegex = new RegExp(`^(${honorifics.join('|')})\\s+`, 'i');

const nameSuffixes = [
  /\b(jr|sr|i{1,3}|iv|v|esq|esquire|cpa|mba|jd|j\.d\.|phd|m\.d\.|md|cfa|cfe|cma|cfp|llb|ll\.b\.|llm|ll\.m\.|rn|np|pa|pmp|pe|p\.eng|cis|cissp|aia|shrm[-\s]?(cp|scp)|phr|sphr|gphr|ra|dds|dmd|do|dc|rd|ot|pt|lmft|lcsw|lpc|lmhc|pcc|acc|mcc|six\s?sigma|ceo|cto|cmo|chro|ret\.?|gen\.?|col\.?|maj\.?|capt?\.?|lt\.?|usa|usaf|usmc|usn|uscg|comp?tia|aws|hon|rev|fr|rabbi|imam|president|founder)\b\.?/i
];

function cleanBusinessName(name) {
  if (!name) return '';
  let cleaned = name.trim();
  for (const suffix of businessSuffixes) {
    cleaned = cleaned.replace(suffix, '').trim();
  }
  return cleaned.replace(/[.,]$/, '').trim();
}

function cleanAndSplitName(raw, businessName = '') {
  if (!raw) return null;
  let clean = raw.replace(honorificRegex, '');
  clean = clean.replace(/[,\/*\\]+$/, '').trim();
  let namePart = clean;
  let titlePart = '';
  if (clean.includes(',')) {
    const [name, ...rest] = clean.split(',');
    namePart = name.trim();
    titlePart = rest.join(',').trim();
  }
  if (!namePart || namePart.toLowerCase() === businessName.toLowerCase()) return null;
  let tokens = namePart.split(/\s+/).filter(Boolean);
  if (tokens.length < 2 || tokens.length > 4) return null;
  // drop trailing suffixlike tokens
  while (tokens.length > 1 && nameSuffixes.some(rx => rx.test(tokens[tokens.length - 1]))) {
    tokens.pop();
  }
  if (tokens.length < 2) return null;
  return {
    'first name': tokens[0],
    'middle name': tokens.length > 2 ? tokens.slice(1, -1).join(' ') : '',
    'last name': tokens[tokens.length - 1],
    'title': titlePart
  };
}

/* ---------------------------
   NDJSON / STORAGE
   --------------------------- */

const allLeads = new Map();

async function loadExistingLeads() {
  if (!fs.existsSync(leadsPath)) return;
  const content = await fsPromises.readFile(leadsPath, 'utf-8');
  const blocks = content.split(/\n\s*\n/);
  for (const block of blocks) {
    if (!block.trim()) continue;
    try {
      const record = JSON.parse(block);
      const url = record['website url'];
      if (url) allLeads.set(url, record);
    } catch (err) {
      console.warn('⚠ Skipping invalid NDJSON block');
    }
  }
  console.log(`🔁 Loaded ${allLeads.size} existing leads`);
}

async function saveAllLeads() {
  const records = Array.from(allLeads.values());
  const ndjson = records.map(obj => JSON.stringify(obj, null, 2)).join('\n\n') + '\n';
  await fsPromises.writeFile(leadsPath, ndjson, 'utf-8');
  console.log(`💾 Saved ${records.length} total leads to ${leadsPath}`);
}

// save single record incrementally (append if new)
async function appendLead(record) {
  // write all at end, but keep incremental save for safety
  await saveAllLeads();
}

/* ---------------------------
   HUMAN-LIKE INTERACTIONS
   --------------------------- */

async function humanScroll(page) {
  const steps = randomBetween(4, 7);
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(randomBetween(200, 900), randomBetween(100, 700));
    await page.evaluate(() => window.scrollBy(0, window.innerHeight * (0.2 + Math.random() * 0.6)));
    await delay(randomBetween(150, 600));
  }
}

/* ---------------------------
   SAFE NAVIGATION WITH RETRIES
   --------------------------- */

async function safeGoto(page, url, opts = {}) {
  const maxRetries = opts.retries ?? 3;
  const backoffBase = opts.backoffBase ?? 800;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // use domcontentloaded by default for speed and reliability
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: opts.timeout ?? 45000 });
      return true;
    } catch (err) {
      console.warn(`⚠ goto attempt ${attempt} failed for ${url}: ${err.message}`);
      if (attempt === maxRetries) {
        console.error(`❌ Failed to navigate ${url} after ${maxRetries} attempts`);
        return false;
      }
      const backoff = backoffBase * attempt + Math.random() * 300;
      await delay(backoff);
    }
  }
  return false;
}

/* ---------------------------
   PROFILE SCRAPE
   --------------------------- */

async function scrapeProfile(page, url) {
  try {
    const ok = await safeGoto(page, url, { timeout: 45000, retries: 2 });
    if (!ok) return null;

    console.log(`🧭 Scraping: ${url}`);
    await delay(randomBetween(900, 2200));
    await humanScroll(page);
    await delay(randomBetween(400, 1000));

    // Try three strategies to extract key fields:
    // 1) Look for embedded JSON in script tags (common)
    // 2) Look for "Visit Website" anchor
    // 3) Fall back to reading visible text and searching patterns

    const data = await page.evaluate(() => {
      // helper inside page
      function firstMatchingScriptValue(key) {
        const scripts = Array.from(document.querySelectorAll('script'));
        for (const s of scripts) {
          try {
            const t = s.textContent || '';
            if (t.includes(key)) {
              // naive JSON extraction attempt
              const m = t.match(new RegExp(`"${key}"\\s*:\\s*"([^"]+)"`));
              if (m) return m[1];
            }
          } catch (e) {
            // ignore
          }
        }
        return '';
      }

      // business name heuristics
      const businessNameFromScript = firstMatchingScriptValue('business_name') ||
        firstMatchingScriptValue('businessName') ||
        '';

      // website anchor
      const websiteAnchor = Array.from(document.querySelectorAll('a'))
        .find(a => /visit website/i.test(a.innerText));
      const website = websiteAnchor ? (websiteAnchor.href || '') : '';

      // principal contact heuristics: look for "Principal Contacts" header nearby
      let principal = '';
      const els = Array.from(document.querySelectorAll('body *'));
      for (let i = 0; i < els.length; i++) {
        const el = els[i];
        if (/Principal Contacts/i.test(el.innerText || '')) {
          // find next text node that looks like a name within next few siblings
          for (let j = i + 1; j < Math.min(i + 8, els.length); j++) {
            const txt = (els[j].innerText || '').trim();
            if (txt && txt.split(/\n/).length <= 3) {
              // pick first reasonable candidate
              principal = txt.split('\n')[0].trim();
              break;
            }
          }
          if (principal) break;
        }
      }

      // fallback: common label "Owner", "Principal", "Contact"
      if (!principal) {
        const prefer = Array.from(document.querySelectorAll('p,div,span,h3,h4'))
          .map(n => n.innerText || '')
          .filter(Boolean)
          .find(t => /\b(Principal|Owner|Contact|Managing|President|Director)\b/i.test(t));
        if (prefer) {
          principal = prefer.split('\n')[0].trim();
        }
      }

      // location: try to find City, ST ZIP pattern
      const bodyText = document.body.innerText || '';
      const locationMatch = bodyText.match(/\b[A-Z][a-z]+(?:[ ]?[A-Za-z'-]+)?,\s[A-Z]{2}\s\d{5}\b/);
      const location = locationMatch ? locationMatch[0] : '';

      // industry: look for "Business Categories" block, fallback empty
      let industry = '';
      const catEl = Array.from(document.querySelectorAll('*'))
        .find(n => /Business Categories|Business Category/i.test(n.innerText || ''));
      if (catEl) {
        // try to pull sibling text
        industry = (catEl.nextElementSibling && catEl.nextElementSibling.innerText) || '';
      } else {
        // fallback: search for "Categories" in text around
        const m = bodyText.match(/Business Categories\s*([\s\S]{0,200})/i);
        industry = m ? m[1].split('\n')[0].trim() : '';
      }

      return {
        businessNameScript: businessNameFromScript,
        principalContact: principal,
        location,
        industry,
        website
      };
    });

    // Normalize business name: prefer the script value but if empty, attempt to extract from page title
    let businessName = data.businessNameScript || '';
    if (!businessName) {
      const title = (await page.title()) || '';
      // attempt to strip "BBB" and other noise
      businessName = title.replace(/\s*\|.*$/,'').replace(/\s*-.*$/,'').trim();
    }
    businessName = cleanBusinessName(businessName);

    // If we don't have website yet, try other anchor strategies
    let website = (data.website || '').trim();
    if (!website) {
      // try a more tolerant approach
      try {
        const href = await page.evaluate(() => {
          const anchors = Array.from(document.querySelectorAll('a'));
          // prefer anchors that contain http and not bbb.org
          const candidate = anchors.find(a => a.href && /https?:\/\//i.test(a.href) && !a.href.includes('bbb.org'));
          return candidate ? candidate.href : '';
        });
        website = href || website;
      } catch (e) {
        // ignore
      }
    }

    // parse and clean the principal contact
    const principalRaw = (data.principalContact || '').replace(/\s+/g, ' ').trim();
    const split = cleanAndSplitName(principalRaw, businessName);

    // If crucial fields are missing, skip
    if (!businessName || !website || !split) {
      console.log('⚠ Incomplete profile (missing businessName/website/contact). Skipping.');
      return null;
    }

    const record = {
      'business name': businessName,
      'website url': website,
      'location': data.location || '',
      'industry': data.industry || '',
      'first name': split['first name'],
      'middle name': split['middle name'],
      'last name': split['last name'],
      'title': split['title'],
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

    return record;
  } catch (err) {
    console.error(`❌ Error scraping profile ${url}: ${err.message}`);
    return null;
  }
}

/* ---------------------------
   MAIN SCRAPE FLOW
   --------------------------- */

(async () => {
  await fsExtra.ensureDir(path.dirname(leadsPath));
  await loadExistingLeads();

  // Launch browser with larger protocol timeout and safe args
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: CHROME_EXECUTABLE,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--no-first-run',
      '--no-zygote',
      '--single-process'
    ],
    // Raised protocol timeout to avoid ProtocolError
    protocolTimeout: 120000, // 120s
    defaultViewport: { width: 1280, height: 800 }
  });

  const page = await browser.newPage();
  // Larger default navigation timeout
  page.setDefaultNavigationTimeout(60000); // 60s

  // iterate search URLs
  for (const baseUrl of SEARCH_URLS) {
    console.log(`\n🔎 Starting search: ${baseUrl}`);
    // detect if baseUrl already has page= query param
    const urlMatch = baseUrl.match(/page=(\d+)/);
    let pageNum = urlMatch ? parseInt(urlMatch[1], 10) : 1;

    while (true) {
      const paginatedUrl = urlMatch ? baseUrl.replace(/page=\d+/, `page=${pageNum}`) : `${baseUrl}&page=${pageNum}`;
      console.log(`🌐 Visiting: ${paginatedUrl}`);

      // navigate with retry
      const ok = await safeGoto(page, paginatedUrl, { timeout: 45000, retries: 2 });
      if (!ok) {
        console.warn('✋ stopping pagination due to navigation failures.');
        break;
      }

      // ensure there are profile links — wait for a reasonable selector or fallback to checking body
      try {
        // prefer CSS selector matching profile cards / profile links
        const found = await page.$('a[href*="/profile/"]');
        if (!found) {
          // try waiting for a common container for search results
          const maybe = await page.$('div.search-results, div.results, section.search-results');
          if (!maybe) {
            console.log('⚠ No profile container found on this page. Stopping pagination.');
            break;
          }
        }
      } catch (e) {
        console.warn('⚠ Error checking for profiles:', e.message);
      }

      await humanScroll(page);

      // gather unique profile links (filter out about pages)
      const profileLinks = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href*="/profile/"]'))
          .map(a => a.href)
          .filter((href, i, arr) => href && !href.includes('/about') && arr.indexOf(href) === i)
      );

      if (!profileLinks || profileLinks.length === 0) {
        console.log(`⚠ No profile links found on page ${pageNum}.`);
        break;
      }

      let newLeadsThisPage = 0;
      for (const link of profileLinks) {
        try {
          // skip duplicates early
          if (allLeads.has(link)) {
            console.log(`⏭ Duplicate profile: ${link}`);
            continue;
          }

          const rec = await scrapeProfile(page, link);
          if (rec) {
            allLeads.set(rec['website url'], rec);
            newLeadsThisPage++;
            console.log(`✅ Added: ${rec['business name']} — ${rec['website url']}`);
            // save incrementally to avoid data loss
            await saveAllLeads();
          } else {
            console.log('⏭ Skipped incomplete or failed profile');
          }
        } catch (err) {
          console.error('❌ Error processing profile link:', err.message);
        }
        // polite pause between profiles
        await delay(randomBetween(900, 2500));
      }

      console.log(`📥 New leads this page: ${newLeadsThisPage}`);

      // basic pagination stop rule: if no new leads found this page and pageNum > 1, stop
      if (newLeadsThisPage === 0 && pageNum > 1) {
        console.log('🔚 No new leads found on this page; stopping pagination for this search.');
        break;
      }

      pageNum++;
      // small pause before loading next page of results
      await delay(randomBetween(800, 2000));
    } // end pagination loop

    console.log(`📌 Finished search: ${baseUrl}`);
    // small delay between search URL batches
    await delay(randomBetween(1200, 3000));
  } // end searchUrls loop

  await browser.close();
  await saveAllLeads();
  console.log('✅ Scraping complete.');
})();
