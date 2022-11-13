import csv
import os
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options  
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import time
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller

chromedriver_autoinstaller.install()

def scrape_all_courses(driver, category_name):

    formatted_name = category_name.lower().replace(" ", "-") # Formats request category
    scrape_url = "https://www.coursera.org/browse/" + formatted_name

    driver.get(scrape_url) # Gets category page
    if driver.title == "": # Checks if page exists
        return None

    print("Scraping all courses from: " + scrape_url)
    
    # Accepts privacy policy
    try:
        time.sleep(2)
        btn_accept = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
        btn_accept.click()
        time.sleep(0.5)
    except:
        pass

    # Loads in the whole page
    print("Loading the page")
    non_loaded_page_height = driver.execute_script("return document.body.scrollHeight")
    body = driver.find_element(By.XPATH, '/html/body')
    while driver.execute_script("return document.body.scrollHeight") <= non_loaded_page_height:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.1)
    
    # Loads in all the course content
    print("Loading the page content")
    btn_elements = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "slick-next")))
    for btn in btn_elements:
        while "slick-disabled" not in btn.get_attribute("class"):
            btn.click()
    time.sleep(4)
    
    print("Gathering courses") # Gathers all available courses
    course_elements = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "collection-product-card")))
    
    print("Filtering courses") # Filters out duplicates and non-applicable pages
    links = [e.get_attribute('href') for e in course_elements]
    filtered_project_links = list(dict.fromkeys([e for e in links if "/projects/" not in e]))
    filtered_certificate_links = [e for e in filtered_project_links if "/professional-certificates/" not in e]
    print("Found " + str(len(filtered_certificate_links)) + " available courses")

    return filtered_certificate_links # Returns found courses


def scrape_course_content(driver, scrape_url):

    driver.get(scrape_url)
    time.sleep(0.5)
    
    # Course category
    try:
        course_navigation = driver.find_elements(By.CLASS_NAME, "_1ruggxy")
        course_category = course_navigation[-1].text
    except StaleElementReferenceException:
        driver.refresh()
        course_navigation = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_1ruggxy")))
        course_category = course_navigation[-1].text
    except:
        course_category = ""
    
    # Course title
    try:
        course_title = driver.find_element(By.CLASS_NAME, "banner-title").text
    except StaleElementReferenceException:
        driver.refresh()
        course_title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "banner-title"))).text
    except:
        course_title = ""

    # First instructor
    try:
        first_instrutor = driver.find_element(By.XPATH, "//div[@class='_1qfi0x77']/div[@class='_1qfi0x77']/span").text
    except NoSuchElementException:
        try:
            first_instrutor = driver.find_element(By.CLASS_NAME, "instructor-count-display").text.split('+')[0]
        except NoSuchElementException:
            first_instrutor = ""
    except StaleElementReferenceException:
        driver.refresh()
        try:
            first_instrutor = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='_1qfi0x77']/div[@class='_1qfi0x77']/span"))).text
        except NoSuchElementException:
            first_instrutor = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "instructor-count-display"))).text.split('+')[0]
    except:
        first_instrutor = ""
    
    # Course description
    try:
        course_description = driver.find_element(By.CLASS_NAME, "description").text.replace('\n', ' ').strip()
    except StaleElementReferenceException:
        driver.refresh()
        course_description = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "description"))).text.replace('\n', ' ').strip()
    except:
        course_description = ""
    
    # numebr of students enrolled
    try:
        num_stud_enrolled = driver.find_element(By.XPATH, "//div[@class='_1fpiay2']/span/strong/span").text.replace(',', '')
    except StaleElementReferenceException:
        driver.refresh()
        num_stud_enrolled = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='_1fpiay2']/span/strong/span"))).text.replace(',', '')
    except:
        num_stud_enrolled = ""
    
    # number of ratings
    try:
        num_ratings = driver.find_element(By.XPATH, "//span[@data-test='ratings-count-without-asterisks']").text.split(' ')[0].replace(',', '')
    except StaleElementReferenceException:
        driver.refresh()
        num_ratings = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[@data-test='ratings-count-without-asterisks']"))).text.split(' ')[0].replace(',', '')
    except:
        num_ratings = ""

    return [course_category, course_title, first_instrutor, course_description, num_stud_enrolled, num_ratings]

def save_results_to_file(scraped_content):
    timestamp = str(int(time.time()))
    csv_location = "results/" + timestamp + ".csv"
    with open(csv_location, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        for e in scraped_content:
            writer.writerow(e)
    return "Result available at /" + csv_location

def run_scraper(category_name):
    scraped_content = []

    print("Initializing web driver")
    op = Options()
    op.add_argument("--headless")
    driver = webdriver.Firefox(options=op)
    driver.set_window_size(800, 600)
    print("Web driver initialized")

    time_start = int(time.time()) # Timing

    # Scrapes eavailable courses from category page
    found_courses = scrape_all_courses(driver, category_name)
    if found_courses == None:
        driver.close()
        return "No category found under \"" + category_name + "\""
    
    # Scrapes content from course pages
    for url in found_courses:
        print("Scraping content from: " + url)
        scraped_course_content = scrape_course_content(driver, url)
        scraped_content.append(scraped_course_content)


    time_end = int(time.time()) # Timing
    print("Time elapsed: " + str(time_end-time_start) + " seconds")

    print("Closing web driver")
    driver.close()

    result_msg = save_results_to_file(scraped_content) # Saves to CSV file

    return result_msg


if __name__ == '__main__':
    test_category = "Data science"
    run_scraper(test_category)