import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

const AIRTABLE_BASE_URL = `https://api.airtable.com/v0/${process.env.AIRTABLE_BASE_ID}/${process.env.SCRAPER_TABLE_NAME}`;
const HEADERS = {
  Authorization: `Bearer ${process.env.AIRTABLE_API_KEY}`,
  'Content-Type': 'application/json'
};

function getDomainFromWebsite(url) {
  try {
    const clean = url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
    return clean.toLowerCase();
  } catch {
    return '';
  }
}

function generatePermutations(first, last, domain) {
  const f = first[0];
  const l = last[0];

  return [
    `${first}.${last}@${domain}`,
    `${first}@${domain}`,
    `${f}${last}@${domain}`,
    `${first}${last}@${domain}`,
    `${last}.${first}@${domain}`,
    `${first}_${last}@${domain}`,
    `${first}${l}@${domain}`,
    `${f}.${last}@${domain}`
  ].map(e => e.toLowerCase());
}

async function fetchMissingRecords(offset = null) {
  const params = new URLSearchParams({
    filterByFormula: `AND({First Name} != '', {Last Name} != '', {website url} != '', NOT({Email Permutations}))`,
    pageSize: 10
  });
  if (offset) params.append('offset', offset);

  const res = await fetch(`${AIRTABLE_BASE_URL}?${params.toString()}`, {
    method: 'GET',
    headers: HEADERS
  });

  if (!res.ok) {
    console.error('❌ Failed to fetch Airtable:', await res.text());
    return { records: [], offset: null };
  }

  return await res.json();
}

async function updateRecord(id, permutations) {
  const body = {
    records: [
      {
        id,
        fields: {
          'Email Permutations': permutations.join(', ')
        }
      }
    ]
  };

  const res = await fetch(AIRTABLE_BASE_URL, {
    method: 'PATCH',
    headers: HEADERS,
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    console.error(`❌ Failed to update ${id}:`, await res.text());
  } else {
    console.log(`✅ Updated record ${id}`);
  }
}

(async () => {
  let offset = null;
  let totalUpdated = 0;

  do {
    const { records, offset: nextOffset } = await fetchMissingRecords(offset);
    if (!records.length) break;

    for (const record of records) {
      const fields = record.fields;
      const id = record.id;

      const first = fields['First Name']?.trim();
      const last = fields['Last Name']?.trim();
      const website = fields['website url']?.trim();

      const domain = getDomainFromWebsite(website);
      if (!first || !last || !domain) continue;

      const perms = generatePermutations(first, last, domain);
      await updateRecord(id, perms);
      totalUpdated++;
    }

    offset = nextOffset;
  } while (offset);

  console.log(`🎯 Done! ${totalUpdated} records updated with permutations.`);
})();
