from config_helper import start, create_config

from datetime import date, timedelta
from time import sleep 
import os
import dummylog

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver import ActionChains

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from dotenv import load_dotenv
load_dotenv(dotenv_path='keys.env')

import ssl 
ssl._create_default_https_context = ssl._create_unverified_context

def setup_page() -> WebDriver:
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--width=1920') 
    options.add_argument('--height=1080') 
    options.add_argument('--start-maximized') 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")

    driver = webdriver.Edge(options=options)
    dl.logger.info('opening selenium')
    driver.get(get_url_for_date(configs['start_date']))
    
    overnight_dropdown = driver.find_elements(By.XPATH, '//*[@id="division-selection"]')
    ActionChains(driver).click(overnight_dropdown[0]).perform()
    ActionChains(driver).send_keys("o").send_keys(Keys.ENTER).perform()

    group_size_dropdown = driver.find_elements(By.ID, "guest-counter-QuotaUsageByMember")
    ActionChains(driver).click(group_size_dropdown[0]).perform()

    group_size_increase = driver.find_elements(By.XPATH, '//*[@id="guest-counter-QuotaUsageByMember-popup"]/div/div[1]/div/div/div/div[2]/div/div/button[2]')
    ActionChains(driver).click(group_size_increase[0]).perform() # 1 person
    ActionChains(driver).click(group_size_increase[0]).perform() # 2 people
    ActionChains(driver).click(group_size_increase[0]).perform() # 3 people
    return driver

def scrape(zone):
    global locations
    pages = (configs['end_date'] - configs['start_date']).days // 10 # numbers of sets of ten days
    remainder = (configs['end_date'] - configs['start_date']).days % 10 # remainder days to read
    found = False
    try:
        driver = setup_page()
        zone_name = driver.find_elements(By.XPATH, f'//*[@id="per-availability-main"]/div/div[4]/div[3]/div[2]/div[2]/div[{zone}]/div[1]')
        locations[zone] = zone_name[0].text.strip()
        for i in range(pages):
            found = found or read_days(driver, zone, i)
            next_5_days_button = driver.find_elements(By.XPATH, '//*[@id="per-availability-main"]/div/div[4]/div[1]/div/div[2]/div/div/button[3]')
            ActionChains(driver).click(next_5_days_button[0]).perform() # jump 5 days
            ActionChains(driver).click(next_5_days_button[0]).perform() # jump 10 days
        found = found or read_days(driver, zone, pages, remainder+1)
    except Exception as e:
        dl.logger.error(e)
    finally:
        driver.quit()
    return found

def read_days(driver, zone, page, days_to_read = 10) -> bool:
    found = False
    for j in range(3, days_to_read + 3): # 10 days visible
        current_date = configs['start_date'] + timedelta(days= page * 10 + j-3)
        permit_days = driver.find_elements(By.XPATH, f'//*[@id="per-availability-main"]/div/div[4]/div[3]/div[2]/div[2]/div[{zone}]/div[{j}]/div/button/span')
        number_available = int(permit_days[0].text.strip())
        print(current_date, ":", number_available, end=", ")
        if number_available != 0:
            dl.logger.info(f'Found {number_available} permit{"" if number_available == 1 else "s"} on {current_date} in {locations[zone]}, sending email')
            send_email(current_date, number_available, locations[zone])
            found = True
    return found

def send_email(current_date: date, number_available:int, location:str):
    emails = configs['to_emails'].split(';')
    message = Mail(
        from_email=os.getenv('FROM_EMAIL'),
        to_emails=emails,
        subject=f'ALERT: {number_available} Enchantments ({location}) permit{"" if number_available == 1 else "s"} available {current_date}',
        html_content=f'<dir><a href={get_url_for_date(current_date)}><strong>GO GET THE PERMIT. GO. PERMIT. NOW.</strong></a></dir>')
    try:
        sg = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        sg.send(message)
        dl.logger.info(f"Email sent to {emails}")
    except Exception as e:
        dl.logger.error(f"Error sending email: {e}")

def get_url_for_date(date) -> str:
    base_url = "https://www.recreation.gov/permits/233273/registration/detailed-availability"
    return f"{base_url}?date={date.strftime('%Y-%m-%d')}"

def __main__():
    global configs
    if not os.path.exists('config.ini'):
        create_config()
    configs = start()

    global locations
    locations = {int(zone):'' for zone in configs['zones'].split(',')} # order in list : name

    global dl
    dl = dummylog.DummyLog()
    dl.logger.info('Log File is Created Successfully')

    while True:
        for zone in locations.keys(): # row 1 = snow zone, row 5 = core 
            if(scrape(zone) == False):
                dl.logger.info(f"No available permits found for {locations[zone]}")
        sleep(30)

if __name__ == "__main__":
    __main__()