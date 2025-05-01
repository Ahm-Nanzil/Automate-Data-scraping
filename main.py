from playwright.sync_api import sync_playwright
import time
import os
import re
from pathlib import Path


def get_chrome_user_data_dir():
    """Get the default Chrome user data directory based on OS"""
    home = Path.home()
    if os.name == "nt":  # Windows
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    elif os.name == "posix":  # macOS/Linux
        if os.path.exists(os.path.join(home, "Library", "Application Support", "Google", "Chrome")):
            return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
        else:
            return os.path.join(home, ".config", "google-chrome")
    return None


def google_search_and_extract_text(search_query="site:instagram.com \"fitness Coach\" \"@gmail.com\"", max_pages=3):
    """
    Search Google with the provided query and extract all visible text from result pages

    Args:
        search_query (str): The search query to use
        max_pages (int): Maximum number of search result pages to process
    """
    # Use fixed paths and settings
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    user_data_dir = get_chrome_user_data_dir()
    profile_path = os.path.join(user_data_dir, "Default")

    print(f"Starting Google search for: {search_query}")
    print(f"Using Chrome at: {chrome_path}")
    print(f"Using profile at: {profile_path}")

    # Create a filename for the output
    timestamp = int(time.time())
    filename = f"google_search_text_{timestamp}.txt"

    with sync_playwright() as p:
        try:
            # Launch Chrome with the user's existing profile
            browser_type = p.chromium
            browser = browser_type.launch_persistent_context(
                user_data_dir=profile_path,
                executable_path=chrome_path,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            # Create a new page
            page = browser.new_page()

            # Add anti-detection script
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """
            page.add_init_script(stealth_js)

            # List to store all text content
            all_text = []

            # Open the search URL for the first page
            url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            print(f"Navigating to: {url}")

            # Visit each page of search results
            current_page = 1

            while current_page <= max_pages:
                # Navigate to the current search page
                page.goto(url, wait_until="networkidle", timeout=60000)
                print(f"Loaded page {current_page} of search results")

                # Wait for content to load
                time.sleep(3)

                # Check for CAPTCHA
                if page.locator("iframe[src*='recaptcha']").count() > 0 or \
                        page.locator("text=Select all images").count() > 0 or \
                        page.locator("text=I'm not a robot").count() > 0:

                    print("\nCAPTCHA detected! Please solve it manually in the browser window.")
                    print("The script will wait up to 5 minutes for you to complete it.")

                    # Wait for main content to appear after CAPTCHA
                    try:
                        page.wait_for_selector("div#search", timeout=300000)  # 5 minute timeout
                        print("CAPTCHA solved. Continuing...")
                    except Exception:
                        print("Timeout waiting for CAPTCHA to be solved.")
                        break

                # Take a screenshot for reference
                page.screenshot(path=f"page_{current_page}_{timestamp}.png")

                # Extract all visible text content from the page (similar to Ctrl+A Copy)
                print("Extracting visible text from page...")

                # Use JavaScript to get all visible text on the page
                # This simulates what you'd get with Ctrl+A and copy
                text_content = page.evaluate("""() => {
                    function isVisible(elem) {
                        if (!elem) return false;
                        const style = window.getComputedStyle(elem);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity !== '0' &&
                               elem.offsetWidth > 0 &&
                               elem.offsetHeight > 0;
                    }

                    function getVisibleText(node) {
                        if (node.nodeType === Node.TEXT_NODE) {
                            return node.nodeValue.trim();
                        }

                        if (node.nodeType !== Node.ELEMENT_NODE) {
                            return '';
                        }

                        // Skip script, style, and hidden elements
                        const tagName = node.tagName.toLowerCase();
                        if (tagName === 'script' || tagName === 'style' || tagName === 'noscript' || !isVisible(node)) {
                            return '';
                        }

                        let text = '';
                        for (const childNode of node.childNodes) {
                            text += getVisibleText(childNode) + ' ';
                        }
                        return text.trim();
                    }

                    return getVisibleText(document.body);
                }""")

                # Clean up the text (remove extra spaces, etc.)
                if text_content:
                    # Remove multiple spaces and newlines
                    cleaned_text = re.sub(r'\\s+', ' ', text_content).strip()
                    all_text.append(f"--- PAGE {current_page} ---\n\n{cleaned_text}\n\n")
                    print(f"Extracted {len(cleaned_text)} characters of text")
                else:
                    print("No text content found on this page")

                # Check if there's a next page button
                next_button = page.locator("a#pnnext")
                if next_button.count() > 0:
                    # Get the URL for the next page
                    url = next_button.get_attribute("href")
                    if not url.startswith("http"):
                        url = "https://www.google.com" + url
                    current_page += 1
                    print(f"Found link to next page: {url}")
                else:
                    print("No more result pages available")
                    break

            # Save all text to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Search Query: {search_query}\n")
                f.write(f"Extraction Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write("\n".join(all_text))

            print(f"\nSearch and extraction complete!")
            print(f"Visible text content saved to: {os.path.abspath(filename)}")

            # Close the browser
            browser.close()
            return filename

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # Try to take an error screenshot
            try:
                page.screenshot(path=f"error_{timestamp}.png")
                print(f"Error screenshot saved as error_{timestamp}.png")
            except:
                pass
            return None


if __name__ == "__main__":
    # Use hardcoded search query directly - no prompts
    search_query = 'site:instagram.com "fitness Coach" "@gmail.com"'
    google_search_and_extract_text(search_query)