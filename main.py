from datetime import date, timedelta
from time import sleep 

import dummylog

import gc
from selenium import webdriver

from selenium.webdriver.edge.options import Options

import shutil

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import ssl 

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='keys.env')

ssl._create_default_https_context = ssl._create_unverified_context

global dl
dl = dummylog.DummyLog()
dl.logger.info('Log File is Created Successfully')

def send_email(current_date: date):
    global dl
    email = os.getenv('TO_EMAIL')
    print(email)
    message = Mail(
        from_email=os.getenv('FROM_EMAIL'),
        to_emails=email,
        subject=f'ALERT: ENCHANTMENTS PERMIT AVAILABLE {current_date}',
        html_content='<strong>GO GET THE PERMIT. GO. PERMIT. NOW.</strong>')
    try:
        sg = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        sg.send(message)
        dl.logger.info(f"Email sent to {email}")
    except Exception as e:
        dl.logger.error(f"Error sending email: {e}")
    
def scrape(previous):
    global dl
    page_url = "https://www.recreation.gov/permits/233273/registration/detailed-availability?date=2025-07-01"

    chrome_is_installed = shutil.which("chrome") is not None

    options = webdriver.ChromeOptions() if chrome_is_installed else Options()

    #options.add_argument('--headless') 
    #options.add_argument('--disable-gpu')  
    options.add_argument('--width=1920') 
    options.add_argument('--height=1080') 
    options.add_argument('--start-maximized') 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")

    if not chrome_is_installed:
        driver = webdriver.Edge(options=options)
    else:
        driver = webdriver.Chrome(options=options)
 
    try:
        dl.logger.info('opening selenium')
        driver.get(page_url)
      
        overnight_dropdown = driver.find_elements(By.XPATH, '//*[@id="division-selection"]')
        ActionChains(driver).click(overnight_dropdown[0]).perform()
        ActionChains(driver).send_keys("o").send_keys(Keys.ENTER).perform()

        group_size_dropdown = driver.find_elements(By.ID, "guest-counter-QuotaUsageByMember")
        ActionChains(driver).click(group_size_dropdown[0]).perform()

        group_size_increase = driver.find_elements(By.XPATH, '//*[@id="guest-counter-QuotaUsageByMember-popup"]/div/div[1]/div/div/div/div[2]/div/div/button[2]')
        ActionChains(driver).click(group_size_increase[0]).perform() # 1 person
        ActionChains(driver).click(group_size_increase[0]).perform() # 2 people
        ActionChains(driver).click(group_size_increase[0]).perform() # 3 people

        start_date = date(2025, 7, 1) # july 1st

        found = False
        location = ['Core Enchantment Zone', 'Alpine Lakes']

        for i in range(9):
            found = False
            zone = driver.find_elements(By.XPATH, '//*[@id="per-availability-main"]/div/div[4]/div[3]/div[2]/div[2]/div[5]/div[1]')
            location[0] = zone[0].text.strip()
            zone = driver.find_elements(By.XPATH, '//*[@id="per-availability-main"]/div/div[4]/div[3]/div[2]/div[2]/div[5]/div[2]')
            location[1] = zone[0].text.strip()

            for j in range(3, 13): # 10 days visible
                current_date = start_date + timedelta(days=j-3)
                permit_days = driver.find_elements(By.XPATH, f'//*[@id="per-availability-main"]/div/div[4]/div[3]/div[2]/div[2]/div[5]/div[{j}]/div/button/span')
                if permit_days[0].text.strip() != '0' and previous[i*10+j-3] == '0':
                    found = True
                    dl.logger.info(f'Found new permit on {current_date}, sending email')
                    send_email(current_date)
                previous[i*10+j-3] = permit_days[0].text.strip()

            next_5_days_button = driver.find_elements(By.XPATH, '//*[@id="per-availability-main"]/div/div[4]/div[1]/div/div[2]/div/div/button[3]')
            ActionChains(driver).click(next_5_days_button[0]).perform() # jump 5 days
            ActionChains(driver).click(next_5_days_button[0]).perform() # jump 10 days
            start_date = start_date + timedelta(days=10)

        if(found == False):
            dl.logger.info(f"No available permits found for {location[0]}, {location[1]}")

    except Exception as e:
        dl.logger.error(e)
    finally:
        driver.quit()
        gc.collect()
    return previous

previous = ['0']*90 # 90 days of permits, all set to 0 (no permits)

while True:
    previous = scrape(previous)
    sleep(30)
