from src.database.repository import ProfileRepository
from src.scrapers.profile_scraper import ProfileScraper

# The target URL for scraping [cite: 216]
LEADERSHIP_URL = "https://amzur.com/leadership-team/"
DB_PATH = "data/profiles.db"

def run_collection_pipeline():
    """
    Orchestrates the data collection and storage process.
    """
    print("--- Starting Knowledge Collection Pipeline ---")

    # 1. Initialize repository and create database tables
    repo = ProfileRepository(db_path=DB_PATH)
    print("Initializing database and creating tables...")
    repo.create_tables()

    # 2. Scrape the leadership page
    scraper = ProfileScraper()
    print(f"Scraping profiles from {LEADERSHIP_URL}...")
    profiles = scraper.scrape_leadership_team(LEADERSHIP_URL)

    if not profiles:
        print("No profiles were found. Exiting.")
        return

    print(f"Successfully scraped {len(profiles)} profiles.")

    # 3. Add profiles to the database
    print("Adding profiles to the knowledge base...")
    for profile in profiles:
        repo.add_profile(profile)
    
    print("--- Knowledge Collection Pipeline Finished ---")
    repo.close()

if __name__ == "__main__":
    run_collection_pipeline()