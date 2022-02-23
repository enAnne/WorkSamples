# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 17:16:27 2022

@author: eeann
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

def getElement(driver,eType,eString,tWait=0,maxWait=10):
    if tWait > 0:
        time.sleep(tWait)
    wait = WebDriverWait(driver, maxWait)
    return wait.until(EC.element_to_be_clickable((eType,eString)))

def elementExists(driver,eType,eString,tWait=0,maxWait=10):
    try: 
        getElement(driver,eType,eString,tWait,maxWait) 
    except TimeoutException:
        return False
    return True

# Open browser
driver = webdriver.Chrome(executable_path=r"C:\Users\eeann\AppData\Local\Microsoft\WindowsApps\chromedriver.exe")
driver.maximize_window()
# Login to Neopets account
driver.get("https://www.neopets.com")
getElement(driver,By.XPATH,"//button[text()='Login']").click()
getElement(driver,By.NAME,"username").send_keys('enAnne') 
getElement(driver,By.NAME,'password').send_keys('en900804') 
getElement(driver,By.XPATH,"//input[@id='loginButton']").click()
# Go to ShapeShifter page
driver.get("https://www.neopets.com/medieval/shapeshifter.phtml")





