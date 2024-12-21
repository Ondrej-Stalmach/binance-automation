import re
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_historical_snapshot_links():
    """
    Retrieves all links to historical snapshots
    from the main page https://coinmarketcap.com/historical/.
    """
    url = "https://coinmarketcap.com/historical/"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <a> tags and select only those pointing to /historical/YYYYMMDD/
    snapshot_links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.startswith("/historical/") and len(href) > len("/historical/"):
            snapshot_links.append("https://coinmarketcap.com" + href)

    # Remove duplicates and sort
    snapshot_links = sorted(set(snapshot_links))
    return snapshot_links

def get_snapshot_data(url):
    """
    For the given snapshot link (url), download the Name and Price of cryptocurrencies
    and return them as a list of dictionaries with the following keys: 'date', 'name', 'price'.
    The website needs to be open, and before extracting the HTML data, it is necessary to scroll 
    down the page slowly, as the data on the site are continuously updated during scrolling (lazy loading).
    """
    # Extract the date (e.g., 20200105 from /historical/20200105/) from the URL
    match = re.search(r'/historical/(\d{6,8})/?', url)
    if match:
        snapshot_date = match.group(1)
    else:
        snapshot_date = None  # or "Unknown"

    # Set Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # headless mód
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # Run webdrive (Chrome)
    driver = webdriver.Chrome(options=chrome_options)  

    # Open website url
    driver.get(url)

    # Get height of the website
    scroll_height = driver.execute_script("return document.body.scrollHeight")

    # Set parameters for scrolling
    total_time = 5
    steps = 50
    pause = total_time / steps

    # Scrolling cycle
    for i in range(steps + 1):
        fraction = i / steps
        position = scroll_height * fraction
        driver.execute_script(f"window.scrollTo(0, {position});")
        time.sleep(pause)
    
    # Get full html
    page_source = driver.page_source
   
    # Parse with the BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # find tbody element and than all tr cmc-table-row elements
    tbody = soup.find("tbody")
    rows = tbody.find_all(
        "tr",
        class_="cmc-table-row", 
    )
    data = []
    for row in rows:
        cells = row.find_all("td", recursive=False)
        symbol_td = cells[2]
        price_td = cells[4]
        symbol_text = symbol_td.get_text(strip=True)
        price_text_raw = price_td.get_text(strip=True)
        price_value = float(price_text_raw.replace("$", "").replace(",", ""))
        data.append({
            "date": snapshot_date,
            "name": symbol_text,
            "price": price_value
        })
    driver.quit()
    return data

def main():
    # 1. Retrieve all links to historical snapshots
    links = get_historical_snapshot_links()

    # 2. Select which link to use
    filtered_links = []
    for link in links:
        # Exctract date from the URL
        match = re.search(r'/historical/(\d{6,8})/?', link)
        if match:
            snapshot_str = match.group(1)  
            snapshot_int = int(snapshot_str)  
            # Check if the link is within the specified interval 
            if 20130601 <= snapshot_int <= 20181231:
                filtered_links.append(link)

    all_data = []
    # 2. For each link, scrape and collect the data
    for link in filtered_links:
        snapshot_data = get_snapshot_data(link)
        all_data.extend(snapshot_data)
        print(link)

    # 3. Save data to a CSV file
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv("coinmarketcap_historical_data.csv", index=False)
        print("Data has been saved to coinmarketcap_historical_data.csv")
    else:
        print("No data could be retrieved.")

if __name__ == "__main__":
    main()
