'''
__author__ = "Chenghuan Liu "
__mail__ = "chenghuan.liu@woodplc.com"
'''

import os
import csv
import time
import logging

from selenium import webdriver  # Selenium tools
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(handlers=[logging.FileHandler('meridium_gui_auto.log'), logging.StreamHandler()],
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
logging.info('-----------------------------------New Session-------------------------------------')


def open_incognito_window(chrome_driver_exe, url, run_selenium_headless):
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("start-maximized")
    if run_selenium_headless:
        options.add_argument('headless')
    options.add_experimental_option('useAutomationExtension', False)
    if chrome_driver_exe:
        driver = webdriver.Chrome(chrome_driver_exe, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver


def find_element(web_driver, value: str, by="xpath", wait_time_sec=90, description="", sleep_time=0):
    # Note 1: Always forgot to put in by, changed it so that it defaults to xpath
    # Note 2: Always forgot to put in // at the front of xpath, added if statement to catch that mistake
    if by not in ['id', 'xpath', 'xpath_multi', 'class']:
        raise Exception(
            f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")

    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            if by == "id":
                return web_driver.find_element_by_id(value)
            elif by == "xpath":
                if value[:2] != "//":
                    logging.error(f"ERROR[find_element] for {value} using {by} // was not set")
                    break
                return web_driver.find_element_by_xpath(value)
            elif by == "xpath_multi":
                if value[:2] != "//":
                    logging.error(f"ERROR[find_element] for {value} using {by} // was not set")
                    break
                return web_driver.find_elements_by_xpath(value)  # will return list
            elif by == "class":
                return web_driver.find_element_by_class_name(value)
            else:
                raise Exception(
                    f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")
        except:
            pass

        if sleep_time:
            time.sleep(sleep_time)


def find_element_and_click(web_driver, value: str, by="xpath", wait_time_sec=120, description="", sleep_time=0):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            element = find_element(web_driver, value, by=by, wait_time_sec=wait_time_sec)
            element.click()
        except:
            pass
        else:
            return

        if sleep_time != 0:
            time.sleep(sleep_time)
    raise Exception(f"couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")


def find_elements_search_for_innerhtml(web_driver, xpath: str, innerhtml: str, action="click", wait_time_sec=120,
                                       description="", upper_case=False):
    # Note 1: Sometimes when searching for innerhtml the document changes and so innerhtml raises an error hence a try except statement is needed
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            elements_list = find_element(web_driver, xpath, by="xpath_multi",
                                         wait_time_sec=2)  # Assume that the list will be short enough to load without typing anything
            for element in elements_list:
                if upper_case:
                    if element.text.upper() == innerhtml.upper():  # Case insensitive
                        if action == "click":
                            element.click()
                            return
                else:
                    if element.text == innerhtml:  # Case insensitive
                        if action == "click":
                            element.click()
                            return
        except:
            pass
    raise Exception(
        f"ERROR[find_element] couldn't find element {description}: {xpath} using with innerHTML of {innerhtml} within {wait_time_sec} seconds")


def find_elements_search_for_innerhtml_then_click(web_driver, xpath: str, innerhtml: str, action="click",
                                                  wait_time_sec=120, description=""):
    # Note 1: Sometimes when searching for innerhtml the document changes and so innerhtml raises an error hence a try except statement is needed
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            elements_list = find_element(web_driver, xpath, by="xpath_multi",
                                         wait_time_sec=2)  # Assume that the list will be short enough to load without typing anything
            for element in elements_list:
                if element.text == innerhtml:
                    if action == "click":
                        element.click()
                        return
        except:
            pass
    raise Exception(
        f"ERROR[find_element] couldn't find element {description}: {xpath} using with innerHTML of {innerhtml} within {wait_time_sec} seconds. Description of element = {description}")


def navigate_to_asi_overview_tab(driver):
    find_element_and_click(driver, "//div[@title='Strategy']", by="xpath", description="Strategy menu left hand pane",
                           wait_time_sec=150)
    print("Found Strategy Btn")
    time.sleep(0.5)  # Little bit of wait to allow loading of data so it doesn't open it in a new tab
    find_element_and_click(driver, "//a[@href='#/asi/overview']", by="xpath",
                           description="Drop down strategy overview from strategy menu")
    print("Found ASI Btn")

def log_into_meridium(url, run_selenium_headless, driver, username, password):
    input_user_id = find_element(driver, "userid", by="id", description="User ID textbox", wait_time_sec=150,
                                 sleep_time=1)
    try:
        input_user_id.send_keys(username)
    except:
        raise Exception(f"ERROR[log_into_meridium] Could not send keys to User ID textbox")

    time.sleep(1)  # Account for slow santos system
    input_password = find_element(driver, "password", by="id", description="Password textbox")

    try:
        input_password.send_keys(password)
    except:
        raise Exception(f"ERROR[log_into_meridium] Could not send keys to Password textbox")

    # no need for this step on the Wood Test Server
    find_elements_search_for_innerhtml_then_click(driver, "//select[@tabindex=3]/option", "APMPROD",
                                                  description="Selecting APMPROD, server which all information is stored")

    # time.sleep(5)  # Account for slow santos system
    find_element_and_click(driver, "//button[@type='submit']", by="xpath")

def create_new_package(driver, row):
    
    # Package ID = ID
    package_id = find_element(driver, "//input[@placeholder='Text input']", by="xpath", description="Package ID")
    try:
        package_id.send_keys(row['Package ID'])
    except:
        raise Exception(f"ERROR[create_new_package] Could not send keys to Package ID textbox")

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ** Ask santos which one to select for SAP Reference **
    find_element_and_click(driver, "//div[@class='layout-control block-group columns-10']//mi-select//i[@class='icon-arrow pull-right']", by="xpath")
    find_element_and_click(driver, "//div[@class='select-outer-container']//p[contains(text(), 'MERIDIUM APM')]", by="xpath")
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # Description = Package ID
    description = find_element(driver, "//textarea[@placeholder='Text area']", by="xpath", description="Description")
    try:
        description.send_keys(row['Package ID'])
    except:
        raise Exception(f"ERROR[create_new_package] Could not send keys to Description textbox")

    # Click save
    find_element_and_click(driver, "//i[@class='icon-save']", by="xpath")

def add_job_plan(driver, row):
    # Job ID = Job Plan
    job_id = find_element(driver, "//div[@class='layout-element-caption block'][contains(text(), 'ID:')]/following::input[1]", by="xpath", description="Job ID")
    try:
        job_id.send_keys(row['Job Plan'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to Job ID textbox")

    # don't fill in plan description

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # myPlant Document number this will match with mydoc number (new column)
    myPlant = find_element(driver, "//div[@class='layout-element-caption block'][contains(text(), 'myPlant Document')]/following::input[1]", by="xpath", description="myPlant Document Number")
    try:
        myPlant.send_keys(row['mydoc'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to myPlant Document Number textbox")
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # oracle activity comes from far right 
    oracle_activity = find_element(driver, "//div[@class='layout-element-caption block'][contains(text(), 'Oracle Activity')]/following::input[1]", by="xpath", description="Oracle Activity")
    try:
        oracle_activity.send_keys(row['oracle activity'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to myPlant Document Number textbox")
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # Click save
    find_element_and_click(driver, "//button[@title='Save']", by="xpath")

def run_selenium_instance(chrome_driver_path, url_home_page, input_csv_list, run_selenium_headless, username,
                          password):
    global error_log
    login_required = True

    unique_package_id_list = list(set([x['package_id'] for x in input_csv_list]))
    packages_created_dic = {p:False for p in unique_package_id_list}

    package_job_plan_dict = {p:[] for p in unique_package_id_list}
    for row in input_csv_list:
        packages_created_dic[row['Package ID']].append(row['Job Plan'])


    for row_index, row in enumerate(input_csv_list):

        start_time = time.time()

        if login_required:
            driver = open_incognito_window(chrome_driver_path, url_home_page, run_selenium_headless)
            driver.implicitly_wait(300)

        try:  # Error handling
            if login_required:
                log_into_meridium(url_home_page, run_selenium_headless, driver, username, password)
                login_required = False

            navigate_to_asi_overview_tab(driver)

            # click create new package 
            find_element_and_click(driver, "//div[@class='block-group page-filter-tools']//button[contains(text(),'New')]", by="xpath")

            if not packages_created_dic[row['Package ID']]:
                create_new_package(driver, row)
                packages_created_dic[row['Package ID']] = True

                for job_plan_idx in range(len(package_job_plan_dict[row['Package ID']])):
                    # click the plus button
                    find_element_and_click(driver, "//section[@class='expanded active border-right']//mi-more-options-noko//i[@class='icon-plus']", by="xpath")

                    # click "Job Plan"
                    find_element_and_click(driver, "//div[@class='more-options-outer-container']//span[contains(text(), 'Job Plan')]", by="xpath")

                    # add new job plan
                    add_job_plan(driver, row)

                    # Go Back
                    find_element_and_click(driver, "//button[@data-action='backInHistory']//i[@class='icon-back-arrow']", by="xpath")
            else:
                continue

            # Once finished job plans go to detais
            find_element_and_click(driver, "//span[contains(text(),'Details')]", by="xpath")


            exit()

        except Exception as e:
            logging.error(e)
            error_log.append(e)
            login_required = True
            driver.quit()
        else:
            pass


def get_input_csv_list(csv_path_file: str):
    if not os.path.exists(csv_path_file):
        raise Exception(f"ERROR[get_input_csv_list] {csv_path_file} does not exist")

    file_obj = open(csv_path_file, "r")
    data_lines = file_obj.readlines()
    file_obj.close()

    ret_list = []

    for i, line in enumerate(data_lines):
        line = line.strip("\n")
        columns = line.split(",")
        if i == 0:
            header_list = columns
            print(header_list)
        else:
            row_dict = {}
            for j in range(len(header_list)):
                row_dict[header_list[j]] = columns[j]
            ret_list.append(row_dict)
    return ret_list


if __name__ == "__main__":
    # Get environmental variables
    username = os.getenv("MERIDIUM_USERNAME")
    password = os.getenv("MERIDIUM_PASSWORD")
    chrome_driver_path = os.getenv("MERIDIUM_CHROME_DRIVER_PATH")
    input_csv_path = os.getenv("MERIDIUM_INPUT_CSV_PATH")
    error_log_path = os.getenv("MERIDIUM_ERROR_LOG_PATH")
    url_home_page = os.getenv("MERIDIUM_URL_HOME_PAGE")

    input_csv_list = get_input_csv_list(input_csv_path)

    error_log = []
    restart_system_error = False

    start_time = time.time()
    run_selenium_headless = False  # must run with display up

    logging.info(f"User Name: \"{username}\"")
    logging.info(f"Start time: {time.ctime(start_time)}")
    logging.info(f"CSV File Path: {input_csv_path}")
    logging.info(f"ChromeDriver Path: {chrome_driver_path}")
    # logging.info(f"Total number of rows to process: {len(floc_asm_list)}")

    run_selenium_instance(chrome_driver_path, url_home_page, input_csv_list, run_selenium_headless, username, password)

    logging.info(f"Finished in {round(time.time() - start_time, 1)}")
