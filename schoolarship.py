import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
import time


def scrape_scholarships(field):
    # Step 1: Perform Google Search
    user_search_query = f"scholarships for {field} students 2024"
    formatted_query = user_search_query.replace(" ", "+")
    search_url = f"https://www.google.com/search?q={formatted_query}&gl=us"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()

        # Step 2: Extract Data from Search Results
        soup = BeautifulSoup(response.text, 'html.parser')
        scholarship_results = []

        # Current Google result containers (June 2024)
        for result in soup.select('div[data-header-feature="0"]'):
            try:
                title = result.select_one('h3').text if result.select_one('h3') else "No title"
                snippet = ""

                # Try multiple selectors for snippet
                for selector in ['.VwiC3b', '.MUxGbd', '.lyLwlc']:
                    if result.select_one(selector):
                        snippet = result.select_one(selector).text
                        break

                # Extract URL
                raw_url = result.select_one('a')['href'] if result.select_one('a') else ""
                url = ""
                if raw_url.startswith('/url?'):
                    parsed = urlparse(raw_url)
                    qs = parse_qs(parsed.query)
                    url = qs.get('q', [''])[0]

                # Filter for scholarship results
                if any(keyword in title.lower() for keyword in ['scholarship', 'grant', 'funding']):
                    # Extract deadline
                    deadline_match = re.search(
                        r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})',
                        snippet, re.IGNORECASE)
                    deadline = deadline_match.group(0) if deadline_match else "Not specified"

                    # Extract amount
                    amount_match = re.search(r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\s*(?:dollars|USD)', snippet,
                                             re.IGNORECASE)
                    amount = amount_match.group(0) if amount_match else "Not specified"

                    # Extract eligibility
                    eligibility_match = re.search(r'(open to|eligible for|for).*?(\.|$)', snippet, re.IGNORECASE)
                    eligibility = eligibility_match.group(0).strip() if eligibility_match else "See website"

                    scholarship_results.append({
                        'title': title,
                        'url': url,
                        'deadline': deadline,
                        'amount': amount,
                        'eligibility': eligibility
                    })
            except Exception as e:
                continue

        # Step 4: Save to File
        output_file = "scholarships.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in scholarship_results:
                f.write(f"Title: {entry['title']}\n")
                f.write(f"URL: {entry['url']}\n")
                f.write(f"Deadline: {entry['deadline']}\n")
                f.write(f"Amount: {entry['amount']}\n")
                f.write(f"Eligibility: {entry['eligibility']}\n\n")

        print(f"Saved {len(scholarship_results)} scholarships to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results: {e}")


if __name__ == "__main__":
    field = input("Enter field of study (e.g., Computer Science): ")
    scrape_scholarships(field)
    time.sleep(2)  # Avoid rapid requests