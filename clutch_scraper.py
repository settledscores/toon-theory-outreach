import requests
from bs4 import BeautifulSoup
import time
import os
from pyairtable import Table
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, TABLE_NAME)

ACCEPTED_LOCATIONS = [
    "United States", "United Kingdom", "Canada", "Australia",
    "Netherlands", "Germany", "Switzerland", "Denmark", "Poland", "Sweden"
]
ACCEPTED_EMPLOYEE_SIZES = ["2-9", "10-49"]
ACCEPTED_INDUSTRIES = [
    "Human Resources", "Consulting", "Sales", "Business Development", "Coaching",
    "Education", "Marketing", "Legal services", "Tax consulting", "Insurance",
    "Law", "HR/Staffing", "Management Consulting", "Sales Consulting"
]

def get_clutch_profiles(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    companies = []

    for company in soup.select(".provider-info"):
        try:
            name = company.select_one("h3 a").text.strip()
            profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
            location = company.select_one(".location").text.strip()
            employees = company.find(text="Employees").find_next().text.strip()
            industry = company.select_one(".field--name-field-service-lines .field__item").text.strip()

            if not any(loc in location for loc in ACCEPTED_LOCATIONS):
                continue
            if not any(size in employees for size in ACCEPTED_EMPLOYEE_SIZES):
                continue
            if not any(niche.lower() in industry.lower() for niche in ACCEPTED_INDUSTRIES):
                continue

            companies.append({
                "name": name,
                "clutch_profile": profile_url,
                "location": location,
                "employees": employees,
                "industry": industry
            })
        except:
            continue

    return companies

def save_to_airtable(companies):
    for company in companies:
        airtable.create({
            "business name": company["name"],
            "clutch profile": company["clutch_profile"],
            "location": company["location"],
            "employee range": company["employees"],
            "industry": company["industry"]
        })
        time.sleep(0.3)  # Rate limit buffer

if __name__ == "__main__":
    # Example URL (adjust this to start at page 1 or paginate through)
    example_url = "https://clutch.co/hr"
    companies = get_clutch_profiles(example_url)
    save_to_airtable(companies)
