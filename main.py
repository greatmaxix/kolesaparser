from numpy.core.records import array
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from urllib.parse import urlencode
import psycopg2
import threading

brandsToBeParsed = [
    'toyota',
    'vaz',
    'mercedes-benz',
    'volkswagen',
    'hyundai',
    'nissan',
]

brandsToBeParsed = [
    'audi',
    'bmw',
    'kia',
    'chevrolet',
    'lexus',
    'daewoo',
]
# 181 pages
def findMaxNumberOfPages(driverWait: WebDriverWait) -> int:
    paginatorContainer = driverWait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'pager')))
    paginatorBtns = paginatorContainer.find_elements_by_xpath('.//ul/li')
    return int(paginatorBtns[-1].text)

def getDbConnection():
    return psycopg2.connect(user='root',
        password='root',
        host="127.0.0.1",
        port="5434",
        database='kolesa_cars')

def insertAppartments(appsData):
    if len(appsData) == 0:
        return

    connection = getDbConnection()
    cursor = connection.cursor()
    records_list_template = ','.join(['%s'] * len(appsData))
    
    insert_query = 'INSERT INTO kolesa_cars (brand, model, year, milleage, city, price, eng_vol, eng_type) VALUES {}'.format(records_list_template)
    cursor.execute(insert_query, appsData)
    connection.commit()
    cursor.close()
    connection.close()


def parseCars(driver, wait, brand):
    filters = {
        'page': 1
    }

    driver.get(rentAppsUrl + brand)
    maxPages = findMaxNumberOfPages(wait)
    for currPage in range(1, maxPages + 1):
        appsDataToWrite = []
        if (currPage > 1):
            filters['page'] = currPage
            driver.get(rentAppsUrl + brand + '?' + urlencode(filters))
        
        # get elements by list of class names
        carCards = driver.find_elements_by_xpath("//div[contains(@class, 'row vw-item list-item')]")

        for currACardTitle in carCards:
            try:
                addText = currACardTitle.find_element_by_xpath(".//div[contains(@class, 'a-search-description')]").text

                model = ''
                year = ''
                milleage = ''
                city = ''
                price = ''
                eng_vol = ''
                eng_type = ''

                # regexp 4 digits followed by ' г.'
                if re.search(r'\d{4} +г', addText):
                    year = re.search(r'\d{4}', addText).group(0)


                if re.search(r'\d+\.\d+ л', addText):
                    eng_vol = re.search(r'\d+\.\d+', addText).group(0)
                elif re.search(r'\d+ л', addText):
                    eng_vol = re.search(r'\d+ л', addText).group(0)
                if re.search(r'\d+км', ("".join(addText.split())) ):
                    milleage = re.search(r'\d+км', ("".join(addText.split())) ).group(0)

                if 'дизель' not in addText:
                    eng_type = 'бензин'
                elif 'газ-бензин' in addText:
                    eng_type = 'газ-бензин'
                elif 'газ' in addText:
                    eng_type = 'газ'
                elif 'бензин' in addText:
                    eng_type = 'бензин'
                elif 'гибрид' in addText:
                    eng_type = 'гибрид'
                elif 'электричество' in addText:
                    eng_type = 'электричество'

                model = ' '.join(currACardTitle.find_element_by_class_name('a-el-info-title').text.split(' ')[1:])
                city = currACardTitle.find_element_by_class_name('list-region').text
                price = re.sub("[^0-9]", "", currACardTitle.find_element_by_class_name('price').text)

                valuesList = [
                    brand,
                    model,
                    year,
                    milleage,
                    city,
                    price,
                    eng_vol,
                    eng_type
                ]
                appsDataToWrite.append(tuple(valuesList))
            except Exception:
                pass

        insertAppartments(appsDataToWrite)

    driver.close()

threads = []
for brand in (brandsToBeParsed):
    driver = webdriver.Chrome(executable_path='C:\Program Files\Google\Chrome\Application\chromedriver.exe')
    wait = WebDriverWait(driver, 5)
    baseUrl = 'https://kolesa.kz/'
    rentAppsUrl = baseUrl + 'cars/'
    thread = threading.Thread(target=parseCars, args=(driver, wait, brand,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()