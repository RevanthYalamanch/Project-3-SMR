import time
from bs4 import BeautifulSoup
from typing import List
from src.database.repository import Profile
# --- NEW IMPORT ---
import undetected_chromedriver as uc
# --- Regular Selenium imports are still needed for waits and exceptions ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class ProfileScraper:
    def scrape_leadership_team(self, url: str) -> List[Profile]:
        """
        Scrapes a highly protected dynamic page using undetected-chromedriver.
        """
        profiles = []
        # --- UNDETECTED CHROME DRIVER SETUP ---
        options = uc.ChromeOptions()
        # You can still run headless once you confirm it works
        # options.add_argument('--headless')
        options.add_argument("start-maximized")

        # The library handles most of the anti-detection tweaks automatically
        driver = uc.Chrome(options=options, use_subprocess=True)

        try:
            print("Navigating to URL with undetected driver...")
            driver.get(url)
            
            # The cookie handling logic can remain the same
            try:
                cookie_button_wait = WebDriverWait(driver, 5)
                accept_button = cookie_button_wait.until(
                    EC.element_to_be_clickable((By.ID, "cn-accept-cookie"))
                )
                print("Cookie banner found. Clicking 'Accept'...")
                accept_button.click()
                time.sleep(1)
            except TimeoutException:
                print("No cookie banner found. Continuing...")

            wait = WebDriverWait(driver, 30)
            
            print("Waiting for profile names to become visible...")
            wait.until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "h3.elementor-team-member-name"))
            )
            print("Profile names are visible. Scraping...")

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            profile_cards = soup.select('.elementor-team-member')
            print(f"DEBUG: Found {len(profile_cards)} profile cards.")

            for card in profile_cards:
                try:
                    name = card.select_one('h3.elementor-team-member-name').get_text(strip=True) if card.select_one('h3.elementor-team-member-name') else "N/A"
                    role = card.select_one('.elementor-team-member-position').get_text(strip=True) if card.select_one('.elementor-team-member-position') else "N/A"
                    photo_tag = card.select_one('img.elementor-team-member-image')
                    photo_url = photo_tag['src'] if photo_tag and photo_tag.has_attr('src') else None
                    bio = f"Profile for {name}, {role}."

                    profile_data = Profile(
                        name=name,
                        role=role,
                        bio=bio,
                        photo_url=photo_url
                    )
                    profiles.append(profile_data)
                except Exception as e:
                    print(f"Could not parse a profile card: {e}")

        except TimeoutException:
            print("\nERROR: Timed out waiting for profiles to load.")
            print("The site may have changed its structure or the anti-scraping is still effective.")
        except Exception as e:
            print(f"An unexpected error occurred during scraping: {e}")
        finally:
            print("Closing browser...")
            driver.quit()
            
        return profiles