def main():
    print("🔄 Starting Manifest scraper (via ScraperAPI)...")
    for page in range(MAX_PAGES):
        url = f"{BASE_URL}?page={page}"
        print(f"🌐 Scraping: {url}")
        html = fetch_with_scraperapi(url)
        if not html:
            continue

        # TEMPORARY: Dump raw HTML to file for inspection
        with open(f"page_{page}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📁 Dumped HTML to page_{page}.html for inspection.")

        soup = BeautifulSoup(html, "html.parser")
        companies = extract_company_data(soup)
        if companies:
            upload_to_airtable(companies)
        time.sleep(60)

    print("🎉 Done.")
