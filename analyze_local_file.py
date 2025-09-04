from bs4 import BeautifulSoup
from src.database.repository import ProfileRepository, Profile
from typing import List

DB_PATH = "data/profiles.db"
LOCAL_HTML_PATH = r"C:\Users\Revanth.REVANTH-SL3\Desktop\Project 3 SMR\data\amzur_leadership.html"

def analyze_and_load():
    """
    Reads the definitive local HTML file, parses it with corrected selectors,
    extracts profile data, and loads it into the database.
    """
    print("--- Starting Local HTML Analysis Pipeline ---")

    print(f"Reading local file: {LOCAL_HTML_PATH}")
    try:
        with open(LOCAL_HTML_PATH, 'r', encoding='utf-8') as f:
            page_source = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found at {LOCAL_HTML_PATH}.")
        return

    soup = BeautifulSoup(page_source, 'html.parser')
    profiles: List[Profile] = []

    # --- CORRECTED SELECTOR ---
    # We select all potential containers and then check if they have a name and image inside.
    # This is a robust way to filter out the empty placeholder divs.
    profile_cards = soup.select('div.e-con-inner > .e-con-full.e-child')
    print(f"Found {len(profile_cards)} potential profile containers.")
    
    successful_extractions = 0
    for card in profile_cards:
        # A valid profile card must contain both a name link and an image.
        name_tag = card.select_one('h4 a')
        img_tag = card.select_one('img')

        if name_tag and img_tag:
            try:
                name = name_tag.get_text(strip=True)
                photo_url = img_tag.get('src')

                # To get the role, we find the container, get all its text,
                # and then remove the name to isolate the role.
                lead_div = card.select_one('div.lead')
                full_text = lead_div.get_text(separator=' ', strip=True)
                role = full_text.replace(name, '').strip()

                profile_data = Profile(
                    name=name,
                    role=role,
                    bio=f"Profile for {name}, {role}.",
                    photo_url=photo_url
                )
                profiles.append(profile_data)
                successful_extractions += 1
            except Exception as e:
                print(f"Could not parse a profile card: {e}")

    if not profiles:
        print("Could not extract any profiles. Check the HTML file and selectors.")
        return

    print(f"Successfully extracted {successful_extractions} profiles.")
    
    # Load the data into the database
    repo = ProfileRepository(db_path=DB_PATH)
    repo.create_tables()
    print("Adding extracted profiles to the database...")
    for profile in profiles:
        repo.add_profile(profile)
    
    print("--- Analysis and Loading Complete ---")
    repo.close()

if __name__ == "__main__":
    analyze_and_load()