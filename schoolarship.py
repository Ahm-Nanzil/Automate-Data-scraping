from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import re
from datetime import datetime


def setup_chrome_driver():
    """Setup Chrome driver with custom profile"""
    options = Options()
    options.binary_location = r"C:\Users\ASUS\Downloads\chrome-win64\chrome-win64\chrome.exe"
    options.add_argument(r"--user-data-dir=C:\Users\ASUS\AppData\Local\Google\Chrome for Testing\User Data")
    options.add_argument(r"--profile-directory=Profile 3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(r"C:\Users\ASUS\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def simple_scholarship_search(search_query="scholarships computer science 2024"):
    """Simple scholarship search - just get scholarship names and universities"""

    print(f"Searching for: {search_query}")
    driver = setup_chrome_driver()

    try:
        # Go to Google
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(5)  # Wait for page to load

        scholarships = []

        # Get all search result titles and links
        results = driver.find_elements(By.CSS_SELECTOR, "h3")

        for result in results:
            try:
                title = result.text.strip()
                if title and is_scholarship(title):
                    # Get the link
                    link_element = result.find_element(By.XPATH, "./parent::a")
                    url = link_element.get_attribute("href")

                    # Extract scholarship name and university
                    scholarship_name = extract_scholarship_name(title)
                    university_name = extract_university_name(title)

                    scholarships.append({
                        'scholarship': scholarship_name,
                        'university': university_name,
                        'url': url
                    })

            except Exception as e:
                continue

        # Save to file
        save_simple_results(scholarships, search_query)
        return scholarships

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

    finally:
        driver.quit()


def is_scholarship(title):
    """Check if title contains scholarship-related words"""
    keywords = ['scholarship', 'grant', 'fellowship', 'award', 'funding']
    return any(keyword.lower() in title.lower() for keyword in keywords)


def extract_scholarship_name(title):
    """Extract scholarship name from title"""
    # Remove common prefixes and clean up
    title = re.sub(r'^(Apply for|Get|Find|Top|Best)\s+', '', title, flags=re.IGNORECASE)

    # If it contains "Scholarship", take everything before " - " or " | "
    if 'scholarship' in title.lower():
        parts = re.split(r'\s*[-|]\s*', title)
        for part in parts:
            if 'scholarship' in part.lower():
                return part.strip()

    return title.strip()


def extract_university_name(title):
    """Extract university name from title"""
    # Common university patterns
    university_patterns = [
        r'(University of [^-|]+)',
        r'([^-|]+ University)',
        r'([^-|]+ College)',
        r'([^-|]+ Institute)',
        r'(MIT|Harvard|Stanford|Yale|Princeton|Columbia|NYU|UCLA|USC)',
    ]

    for pattern in university_patterns:
        matches = re.findall(pattern, title, re.IGNORECASE)
        if matches:
            return matches[0].strip()

    # If no university found, try to extract from parts after "-" or "|"
    parts = re.split(r'\s*[-|]\s*', title)
    if len(parts) > 1:
        return parts[-1].strip()

    return "Not specified"


def save_simple_results(scholarships, search_query):
    """Save simple results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scholarships_simple_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Scholarship Search Results\n")
        f.write(f"Search: {search_query}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

        for i, item in enumerate(scholarships, 1):
            f.write(f"{i}. Scholarship: {item['scholarship']}\n")
            f.write(f"   University: {item['university']}\n")
            f.write(f"   URL: {item['url']}\n\n")

    print(f"Saved {len(scholarships)} results to {filename}")


if __name__ == "__main__":
    query = input("Enter search query (or press Enter for default): ").strip()
    if not query:
        query = "computer science scholarships 2024"

    results = simple_scholarship_search(query)
    print(f"Found {len(results)} scholarships")