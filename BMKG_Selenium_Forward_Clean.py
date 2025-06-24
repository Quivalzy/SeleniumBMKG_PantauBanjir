from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import datetime
import math
from selenium.webdriver.common.action_chains import ActionChains
from seleniumwire import webdriver
from time import process_time

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--disable-cache')
chrome_options.add_experimental_option("detach", True)

# Set up the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.get("https://awscenter.bmkg.go.id/")
driver.maximize_window()
time.sleep(5)
print("Connected to " + driver.title)

element = driver.find_element(By.ID, "icon-login")
element.click()

try: 
    divlogin = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "div-login"))
    )

    search = driver.find_element(By.NAME,"username")
    search.send_keys("XXXXX")
    time.sleep(1)

    search = driver.find_element(By.NAME,"password")
    search.send_keys("XXXXXX")

    search = driver.find_element(By.NAME,"captcha")
    search.send_keys("6")

    search.send_keys(Keys.RETURN)

    act = ActionChains(driver)
    sidebar = driver.find_element(By.CLASS_NAME, "page-sidebar")
    act.move_to_element(sidebar).perform()

    linkData = driver.find_element(By.LINK_TEXT, "Acces Data")
    linkData.click()

    rawData = driver.find_element(By.LINK_TEXT, "Raw Data")
    rawData.click()

    tipe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tipe_alat"))
    )
    tipeAlat = Select(driver.find_element(By.ID, "tipe_alat"))
    tipeAlat.select_by_visible_text("ARG")
    time.sleep(3)

    station = driver.find_element(By.ID, "stasiun")
    allStations = station.find_elements(By.TAG_NAME, "option")
    staSelect = Select(driver.find_element(By.ID, "stasiun"))
    i = 0
    items = [
        "STA0234 - ARG Manimere",
    ]
    while(i<len(items)):
        staSelect.select_by_visible_text(items[i])
        print("Start at:", datetime.datetime.now())
        print("Station Index: "+str(i))
        print("Station Name: "+items[i])
        # startTime = process_time()
        year = 2016
        endDate = 31
        thirtyDaysMonths = [4, 6, 9, 11]
        while(year<=2025):
            month = 1
            if (year == 2025):
                monthLimit = 5
            else:
                monthLimit = 13
            while(month<monthLimit):
                if(month == 2):
                    if(year / 4 == 0):
                        endDate = 29
                    else:
                        endDate = 28
                elif(month in thirtyDaysMonths):
                    endDate = 30
                else:
                    endDate = 31
                
                tanggalAwal = driver.find_element(By.ID, "start")
                tanggalAwal.send_keys(str(year)+"-"+str(month)+"-01")
                tanggalAkhir = driver.find_element(By.ID, "end")
                tanggalAkhir.send_keys(str(year)+"-"+str(month)+"-"+str(endDate))
                submitBtn = driver.find_element(By.ID, "btn-submit")
                submitBtn.click()
                downloadData = WebDriverWait(driver, 999999).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Download Data"))
                )
                trueTble = driver.find_elements(By.CLASS_NAME, "even")
                if(len(trueTble) != 0):
                    downloadData.click()
                    month += 1
                    tanggalAwal.clear()
                    tanggalAkhir.clear()
                else:
                    month += 1
                    tanggalAwal.clear()
                    tanggalAkhir.clear()

                # if(month>5 and year == 2023):
                #     break
                
            year += 1
        
        # stopTime = process_time()
        # runTime = stopTime - startTime
        # runTimeMin = math.floor(runTime/60.0)
        # runTimeSecs = runTimeMin % 60
        

        print("Success")
        print("Finished at:", datetime.datetime.now())
        # print("Finished in " + str(runTimeMin) + " minute(s) and "+ str(runTimeSecs) + " seconds.")
        print("")
        i += 1

except:
    print("Error")