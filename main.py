from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import os
import random
import subprocess
import json
from pathlib import Path
from urllib.parse import quote_plus


def get_chrome_user_data_dir():
    """Get the default Chrome user data directory based on OS"""
    home = Path.home()
    if os.name == "nt":  # Windows
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    elif os.name == "posix":  # MacOS/Linux
        if os.path.exists(os.path.join(home, "Library", "Application Support", "Google", "Chrome")):
            return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
        else:
            return os.path.join(home, ".config", "google-chrome")
    return None


def search_restaurants(query="restaurants near me", location="", num_results=5, chrome_path=None, profile_dir=None):
    """
    Search for restaurants on Google using Playwright with existing Chrome profile

    Args:
        query (str): Search query (default: "restaurants near me")
        location (str): Optional location to add to the query
        num_results (int): Number of search results to save
        chrome_path (str): Path to Chrome executable
        profile_dir (str): Path to Chrome user data directory
    """
    # Combine query and location if provided
    search_query = query
    if location:
        search_query += f" in {location}"

    # Format the query for URL
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    print(f"Searching for: {search_query}")
    print(f"URL: {url}")

    # Create a filename based on the search query
    filename = f"restaurant_search_{int(time.time())}.txt"

    # Use default Chrome user data directory if not specified
    if not profile_dir:
        profile_dir = get_chrome_user_data_dir()
        if not profile_dir:
            print("Error: Could not determine Chrome user data directory.")
            return None

    print(f"Using Chrome profile from: {profile_dir}")

    with sync_playwright() as p:
        try:
            # Launch Chrome with the user's existing profile
            print("Launching Chrome with your existing profile...")
            browser_type = p.chromium

            # Check if chrome_path was provided or use default
            if chrome_path:
                print(f"Using Chrome executable at: {chrome_path}")
                browser = browser_type.launch_persistent_context(
                    user_data_dir=profile_dir,
                    executable_path=chrome_path,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )
            else:
                browser = browser_type.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )

            # Create a new page
            page = browser.new_page()

            # Add anti-bot measures
            # This script removes navigator.webdriver flag (a common bot detection method)
            print("Applying anti-detection measures...")
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });

                // Overwrite the plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Overwrite the languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                // Mask automation
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """
            page.add_init_script(stealth_js)

            # Navigate to search URL
            print("Navigating to Google search...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page loaded.")

            # Add a slight delay for page to fully render
            time.sleep(3)

            # Take a screenshot for debugging
            screenshot_path = f"search_page_{int(time.time())}.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved as {screenshot_path}")

            # Check for CAPTCHA and handle it if needed
            if page.locator("iframe[src*='recaptcha']").count() > 0 or \
                    page.locator("text=Select all images").count() > 0 or \
                    page.locator("text=I'm not a robot").count() > 0:

                print("\nCAPTCHA detected! Please solve it manually in the browser window.")
                print("The script will wait until you complete the CAPTCHA challenge (up to 5 minutes).")

                # Wait for search results to appear after CAPTCHA is solved
                try:
                    page.wait_for_selector("div#search", timeout=300000)  # 5 minute timeout
                    print("CAPTCHA solved and search results loaded.")
                except PlaywrightTimeoutError:
                    print("Timeout waiting for CAPTCHA to be solved.")
                    return None

            # Wait for search results to fully load
            print("Waiting for search results to fully load...")
            try:
                # Try to wait for search results to appear
                page.wait_for_selector("div#search", timeout=30000)
                print("Search results loaded.")
            except PlaywrightTimeoutError:
                print("Timeout waiting for search results, but continuing anyway...")

            # Save the content to a text file
            print("Saving search results to file...")
            with open(filename, 'w', encoding='utf-8') as file:
                # Write the search query and timestamp
                file.write(f"Search Query: {search_query}\n")
                file.write(f"Search Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("-" * 50 + "\n\n")

                # Try to extract search results
                search_results = []

                # Try different selectors that Google might use for search results
                for selector in ["div.g", "div[data-sokoban-container]", "div.Gx5Zad", "div.tF2Cxc"]:
                    results = page.locator(selector)
                    if results.count() > 0:
                        search_results = results
                        print(f"Found {results.count()} results using selector: {selector}")
                        break

                # Extract and save results
                if search_results and search_results.count() > 0:
                    count = min(search_results.count(), num_results)

                    for i in range(count):
                        try:
                            result = search_results.nth(i)

                            # Extract title using various potential selectors
                            title = "No Title Found"
                            for title_selector in ["h3", "h3.LC20lb", "div.yuRUbf h3"]:
                                title_element = result.locator(title_selector).first
                                if title_element.count() > 0:
                                    title = title_element.text_content().strip()
                                    break

                            # Extract link
                            link = "No Link Found"
                            for link_selector in ["a", "div.yuRUbf a", "div.egMi0 a"]:
                                link_element = result.locator(link_selector).first
                                if link_element.count() > 0:
                                    href = link_element.get_attribute("href")
                                    if href:
                                        link = href
                                        break

                            # Extract snippet
                            snippet = "No Snippet Found"
                            for snippet_selector in ["div.VwiC3b", "div.lyLwlc", "span.aCOpRe"]:
                                snippet_element = result.locator(snippet_selector).first
                                if snippet_element.count() > 0:
                                    snippet = snippet_element.text_content().strip()
                                    break

                            # Write the result to the file
                            file.write(f"Result #{i + 1}\n")
                            file.write(f"Title: {title}\n")
                            file.write(f"Link: {link}\n")
                            file.write(f"Snippet: {snippet}\n")
                            file.write("-" * 50 + "\n\n")

                        except Exception as e:
                            file.write(f"Error extracting result #{i + 1}: {str(e)}\n")
                            file.write("-" * 50 + "\n\n")
                else:
                    file.write(
                        "No search results could be extracted. The page structure may have changed or results are not available.\n\n")

                # Also write the full HTML content
                file.write("FULL PAGE CONTENT:\n")
                file.write("=" * 50 + "\n\n")
                file.write(page.content())

            print(f"Search completed. Results saved to {filename}")

            # Close the browser
            browser.close()
            return filename

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # Take a screenshot to help debug the issue
            try:
                page.screenshot(path=f"error_screenshot_{int(time.time())}.png")
                print(f"Error screenshot saved")
            except:
                print("Could not save error screenshot")
            return None


def list_chrome_profiles(user_data_dir):
    """List available Chrome profiles for the user to choose from"""
    profiles = []
    try:
        # Look for Profile directories and the Default profile
        default_profile = os.path.join(user_data_dir, "Default")
        if os.path.exists(default_profile):
            profiles.append(("Default", default_profile))

        # Look for numbered profiles
        for item in os.listdir(user_data_dir):
            if item.startswith("Profile ") and os.path.isdir(os.path.join(user_data_dir, item)):
                profiles.append((item, os.path.join(user_data_dir, item)))

        return profiles
    except Exception as e:
        print(f"Error listing Chrome profiles: {str(e)}")
        return []


def main():
    """Main function to run the restaurant search"""
    print("Google Restaurant Search using Your Chrome Profile")
    print("=" * 45)

    # Get Chrome executable path
    default_chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    chrome_path = input(f"Enter Chrome executable path (default: {default_chrome_path}): ") or default_chrome_path

    # Get or detect Chrome user data directory
    default_user_data_dir = get_chrome_user_data_dir()
    user_data_dir = input(
        f"Enter Chrome user data directory (default: {default_user_data_dir}): ") or default_user_data_dir

    # List available profiles
    profiles = list_chrome_profiles(user_data_dir)
    if profiles:
        print("\nAvailable Chrome profiles:")
        for i, (name, path) in enumerate(profiles):
            print(f"{i + 1}. {name}")

        try:
            profile_index = int(input("\nSelect profile number (default: 1): ") or "1") - 1
            if 0 <= profile_index < len(profiles):
                profile_name, profile_path = profiles[profile_index]
                print(f"Using profile: {profile_name}")
            else:
                print("Invalid selection. Using Default profile.")
                profile_path = os.path.join(user_data_dir, "Default")
        except ValueError:
            print("Invalid input. Using Default profile.")
            profile_path = os.path.join(user_data_dir, "Default")
    else:
        print("No Chrome profiles found. Using Default profile.")
        profile_path = os.path.join(user_data_dir, "Default")

    # Get search parameters from user
    query = input("\nEnter search query (default: 'restaurants near me'): ") or "restaurants near me"
    location = input("Enter location (optional, press Enter to skip): ")

    try:
        num_results = int(input("Number of results to extract (default: 5): ") or "5")
    except ValueError:
        num_results = 5
        print("Invalid input. Using default value: 5")

    # Perform the search
    filename = search_restaurants(query, location, num_results, chrome_path, profile_path)

    if filename:
        print(f"\nSearch completed successfully!")
        print(f"Results saved to: {os.path.abspath(filename)}")
    else:
        print("\nSearch failed. Please try again later.")


if __name__ == "__main__":
    main()