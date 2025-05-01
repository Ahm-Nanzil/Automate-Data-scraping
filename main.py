from playwright.sync_api import sync_playwright

def search_google(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.google.com")

        # Accept cookies if needed
        try:
            page.click('button:has-text("I agree")')
        except:
            pass  # Skip if not shown

        # Perform search
        page.fill("input[name='q']", query)
        page.keyboard.press("Enter")
        page.wait_for_selector("h3")

        # Extract search results
        results = page.query_selector_all("div.g")
        search_data = []

        for r in results:
            try:
                title = r.query_selector("h3").inner_text()
                link = r.query_selector("a").get_attribute("href")
                snippet_el = r.query_selector("span.aCOpRe")
                snippet = snippet_el.inner_text() if snippet_el else ""
                search_data.append({"title": title, "link": link, "snippet": snippet})
            except:
                continue

        browser.close()

        # Save results
        with open("google_results.txt", "w", encoding="utf-8") as f:
            for item in search_data:
                f.write(f"Title: {item['title']}\n")
                f.write(f"Link: {item['link']}\n")
                f.write(f"Snippet: {item['snippet']}\n")
                f.write("\n" + "-"*50 + "\n")

        print("Saved results to google_results.txt")

# Example: search for Instagram profile
search_google("site:instagram.com openai")
