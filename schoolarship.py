import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs


def scrape_scholarships(field):
    # Step 1: Perform Google Search
    user_search_query = f"scholarships for {field} students 2024"
    formatted_query = user_search_query.replace(" ", "+")
    search_url = f"https://www.google.com/search?q={formatted_query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()

        # Step 2: Extract Data from Search Results
        soup = BeautifulSoup(response.text, 'html.parser')
        scholarship_results = []

        for result in soup.select('div.g'):
            try:
                title = result.select_one('h3').text if result.select_one('h3') else "No title"
                snippet = result.select_one('.VwiC3b').text if result.select_one('.VwiC3b') else ""
                raw_url = result.select_one('a')['href'] if result.select_one('a') else ""

                # Clean URL
                url = ""
                if raw_url.startswith('/url?'):
                    parsed = urlparse(raw_url)
                    qs = parse_qs(parsed.query)
                    url = qs.get('q', [''])[0]

                # Step 3: Filter & Clean Data
                if any(keyword in title.lower() for keyword in ['scholarship', 'grant', 'funding']):
                    # Extract deadline (simple pattern)
                    deadline_match = re.search(
                        r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})',
                        snippet)
                    deadline = deadline_match.group(0) if deadline_match else "Not specified"

                    # Extract amount
                    amount_match = re.search(r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\s*(?:dollars|USD)', snippet)
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
                print(f"Error processing result: {e}")
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