from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Target URL
URL = "https://tldb.info/server-status"


def fetch_server_info():
    # Configure headless browser
    options = Options()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Launch Chrome WebDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        # Open the URL
        driver.get(URL)
        time.sleep(3)  # Wait for JavaScript to load

        # Extract Server Status
        server_status = driver.find_element(
            By.CSS_SELECTOR,
            "#svelte > div.container.mt-3\!.container-mb.my-auto\!.svelte-5z85iq > div.container > div > div.item-table.table\! > div > section > article > table > tbody > tr:nth-child(4) > td.text-center > span",
        ).text

        # Extract World
        world = driver.find_element(
            By.CSS_SELECTOR,
            "#svelte > div.container.mt-3\\!.container-mb.my-auto\\!.svelte-5z85iq > div.container > div > div.item-table.table\\! > div > section > article > table > tbody > tr:nth-child(11) > td:nth-child(2) > div > span.mx-1.fw-semi-bold.text-truncate.world-name",
        ).text

        # Extract Region
        region = driver.find_element(
            By.CSS_SELECTOR,
            "#svelte > div.container.mt-3\\!.container-mb.my-auto\\!.svelte-5z85iq > div.container > div > div.item-table.table\\! > div > section > article > table > tbody > tr:nth-child(13) > td.text-muted-light.fw-semi-bold\\!.text-start",
        ).text

        print(f"Server Status: {server_status}")
        print(f"World: {world}")
        print(f"Region: {region}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


# Run the function
fetch_server_info()
