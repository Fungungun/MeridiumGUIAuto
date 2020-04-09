'''
__author__ = "Chenghuan Liu "
__mail__ = "chenghuan.liu@woodplc.com"
'''

import os
import csv
import time
import logging
import pandas as pd

from selenium import webdriver  # Selenium tools
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from dotenv import load_dotenv
import re
from selenium.common import exceptions  


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


def find_element(driver, value: str, by="xpath", wait_time_sec=90, description="", sleep_time=0):
    # Note 1: Always forgot to put in by, changed it so that it defaults to xpath
    # Note 2: Always forgot to put in // at the front of xpath, added if statement to catch that mistake
    # Note 3: There is a WebDriverWait function which allows for cpu to not be churned using a while loop
    try:
        if by == "id":
            element_present = EC.presence_of_element_located((By.ID, value))
            WebDriverWait(driver, wait_time_sec).until(element_present)
            return driver.find_element_by_id(value), EC.presence_of_element_located((By.ID, value))
        elif by == "xpath":
            if value[:2] != "//":
                logging.error(f"ERROR[find_element] for {value} using {by} // was not set")
                raise Exception(f"ERROR[find_element] for {value} using {by} // was not set")
            element_present = EC.presence_of_element_located((By.XPATH, value))
            WebDriverWait(driver, wait_time_sec).until(element_present)
            return driver.find_element_by_xpath(value), EC.presence_of_element_located((By.XPATH, value))
        elif by == "xpath_multi":
            if value[:2] != "//":
                logging.error(f"ERROR[find_element] for {value} using {by} // was not set")
                raise Exception(f"ERROR[find_element] for {value} using {by} // was not set")
            element_present = EC.presence_of_element_located((By.XPATH, value))
            WebDriverWait(driver, wait_time_sec).until(element_present)
            return driver.find_elements_by_xpath(value), EC.presence_of_element_located(
                (By.XPATH, value))  # will return list
        elif by == "class":
            element_present = EC.presence_of_element_located((By.CLASS_NAME, value))
            WebDriverWait(driver, wait_time_sec).until(element_present)
            return driver.find_element_by_class_name(value), EC.presence_of_element_located((By.CLASS_NAME, value))
        else:
            raise Exception(f"ERROR[find_element] By: |{by}| was not out of the options for {value}|{description}")
    except:
        raise Exception(f"ERROR[find_element] By: |{by}| was not out of the options for {value}|{description}")
    return None, None


def find_element_and_click(driver, value: str, by="xpath", wait_time_sec=120, description="", sleep_time=0):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        element, element_clickable = find_element(driver, value, by=by, wait_time_sec=wait_time_sec)
        time_left = wait_time_sec - (time.time() - start_time)
        WebDriverWait(driver, time_left).until(element_clickable)
        try:
            element.click()
            return
        except:
            pass
    raise Exception(f"ERROR[find_element_and_click]: |{value}|{description}| was not clickable")


def find_elements_search_for_innerhtml(web_driver, xpath: str, innerhtml: str, action="click", wait_time_sec=120,
                                       description="", upper_case=False):
    # Note 1: Sometimes when searching for innerhtml the document changes and so innerhtml raises an error hence a try except statement is needed
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            elements_list, _ = find_element(web_driver, xpath, by="xpath_multi",
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
            elements_list, _ = find_element(web_driver, xpath, by="xpath_multi",
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
    time.sleep(0.5)  # Little bit of wait to allow loading of data so it doesn't open it in a new tab
    find_element_and_click(driver, "//a[@href='#/asi/overview']", by="xpath",
                           description="Drop down strategy overview from strategy menu")



def log_into_meridium(url, run_selenium_headless, driver, username, password):
    input_user_id, _ = find_element(driver, "userid", by="id", description="User ID textbox", wait_time_sec=150,
                                 sleep_time=1)
    try:
        input_user_id.send_keys(username)
    except:
        raise Exception(f"ERROR[log_into_meridium] Could not send keys to User ID textbox")

    time.sleep(1)  # Account for slow santos system
    input_password, _ = find_element(driver, "password", by="id", description="Password textbox")

    try:
        input_password.send_keys(password)
    except:
        raise Exception(f"ERROR[log_into_meridium] Could not send keys to Password textbox")

    # no need for this step on the Wood Test Server
    find_elements_search_for_innerhtml_then_click(driver, "//select[@tabindex=3]/option", "APMPROD",
                                                  description="Selecting APMPROD, server which all information is stored")

    
    find_element_and_click(driver, "//button[@type='submit']", by="xpath")


def create_new_package(driver, package_id):
    # Package ID = ID
    package_id_input, _ = find_element(driver, "//input[@placeholder='Text input']", by="xpath", description="Package ID")
    logging.info("Send package ID")
    try:
        package_id_input.send_keys(package_id)
    except:
        raise Exception(f"ERROR[create_new_package] Could not send keys to Package ID textbox")

    # SAP Reference
    find_element_and_click(driver,
                           "//div[@class='layout-control block-group columns-10']//mi-select//i[@class='icon-arrow pull-right']",
                           by="xpath")
    find_element_and_click(driver, "//div[@class='select-outer-container']//p[contains(text(), 'OeAM2')]", by="xpath")
    logging.info("Select SAP Reference")
    # Description = Package ID
    description, _ = find_element(driver, "//textarea[@placeholder='Text area']", by="xpath", description="Description")
    try:
        description.send_keys(package_id)
    except:
        raise Exception(f"ERROR[create_new_package] Could not send keys to Description textbox")
    logging.info("Send description")
    # Click save    
    find_element_and_click(driver, "//i[@class='icon-save']", by="xpath")
    logging.info("Click Save")

def add_job_plan(driver, row):
    # Job ID = Job Plan
    job_id, _ = find_element(driver,
                          "//div[@class='layout-element-caption block'][contains(text(), 'ID:')]/following::input[1]",
                          by="xpath", description="Job ID")
    logging.info("Send job id")
    try:
        job_id.send_keys(row['Job Plan ID'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to Job ID textbox")

    # Plan Description
    plan_description, _ = find_element(driver,
                                    "//div[@class='layout-element-caption block'][contains(text(), 'Plan Description')]/following::textarea[1]",
                                    by="xpath", description="Plan Descriptionr")
    logging.info("Send plan description")
    try:
        plan_description.send_keys(row['Plan Description'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to Plan Description textbox")

    # myPlant Document number this will match with mydoc number (new column)
    myPlant, _ = find_element(driver,
                           "//div[@class='layout-element-caption block'][contains(text(), 'myPlant Document')]/following::input[1]",
                           by="xpath", description="myPlant Document Number")
    logging.info("Send my plant document number")
    try:
        myPlant.send_keys(row['MyPlant Document Number'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to myPlant Document Number textbox")

    # oracle activity comes from far right
    oracle_activity, _ = find_element(driver,
                                   "//div[@class='layout-element-caption block'][contains(text(), 'Oracle Activity')]/following::input[1]",
                                   by="xpath", description="Oracle Activity")
    logging.info("Send oracle activity")
    try:
        oracle_activity.send_keys(row['Oracle Activity'])
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to myPlant Document Number textbox")

    # Click save
    find_element_and_click(driver, "//button[@title='Save']", by="xpath")
    logging.info("Click save button")

def remove_special_characters(input_str):
    return re.sub('[^A-Za-z0-9]+', ' ', input_str)


def link_actions_to_jobplan(driver, job_plan_data):
    # Get all the action names
    action_name_list = job_plan_data["Action Name"].unique().tolist()
    action_name_list = [remove_special_characters(x) for x in action_name_list]
    logging.info(f"link {action_name_list} to this job plan")

    # Click Linked Actions
    find_element_and_click(driver, "//span[contains(text(),'Linked Actions')]", by="xpath")
    logging.info("Click linked actions")

    # Click the plus button
    find_element_and_click(driver, "//button[@data-action='link-action']//i[@class='icon-plus']", by="xpath")
    logging.info("Click the plus button")

    # get all the rows
    potential_action_check_box_list = driver.find_elements_by_xpath("//tbody//tr[@class='dx-row dx-data-row dx-column-lines'][@role='row']//td[@aria-colindex='1']//span[@class='dx-checkbox-icon']")
    logging.info("Get all the check box")
    potential_action_name_list = driver.find_elements_by_xpath("//tbody//tr[@class='dx-row dx-data-row dx-column-lines'][@role='row']//td[@aria-colindex='2']")
    logging.info("Get all the action names")

    assert (len(potential_action_check_box_list) == len(potential_action_name_list))
    logging.info("Number of rows assertion passed")

    selected_actions = []
    for i in range(len(potential_action_check_box_list)):
        potential_action_name = remove_special_characters(potential_action_name_list[i].text)
        if potential_action_name in action_name_list:
            selected_actions.append(potential_action_name)
            potential_action_check_box_list[i].click()
            logging.info(f"'{potential_action_name}' found in action name list {action_name_list} - Select this action ")
        else:
            logging.info(f"'{potential_action_name}' not in action name list {action_name_list} - Skip this action ")
            
    logging.info(f"Selected action {selected_actions} for this job plan")
    # Click the Link button
    if len(selected_actions) > 0:
        find_element_and_click(driver, "//button//span[contains(text(),'Link')]", by="xpath")
        logging.info("click the link button")
    else:
        find_element_and_click(driver, "//button//span[contains(text(),'Cancel')]", by="xpath")
        logging.info("No action selected. Click the cancel button")
    


def manage_actions_with_floc(driver, asset):

    # click the plus button
    find_element_and_click(driver, "//button[@title='Add Actions']//i", by="xpath")
    logging.info("click the plus button")

    # click the search button
    find_element_and_click(driver, "//div[@class='add-bulk-actions']//i[@class='icon-search']", by="xpath")
    logging.info("click the search button")

    # search with floc text area
    asset_name, _ = find_element(driver,
                                "//td[@aria-label='Column Asset, Filter cell']//input",
                                by="xpath", description="asset name")
    logging.info("find asset text area")
    try:
        # asset_name.send_keys(Keys.CONTROL + "a")
        # asset_name.send_keys(Keys.DELETE)
        asset_name.send_keys(asset)
        logging.info("send keys to asset text area")
    except:
        raise Exception(f"ERROR[add_job_plan] Could not send keys to asset textbox")

    no_data = False
    while True:  # this is to make sure the search is finish
        try:
            # results found
            all_returned_records = driver.find_elements_by_xpath("//div[@class='add-bulk-actions-container']//td[@aria-colindex='3']")
            n_records = len(all_returned_records) - 2 # remove heading and empty area
            logging.info(f"Found {n_records} rows for this floc")
            if n_records > 0:
                logging.info("Got actions, search for the first row")
                first_filter_result, _ = find_element(driver, "//div[@class='add-bulk-actions-container']//tr[@aria-rowindex='1']//td[@aria-colindex='3']", by="xpath",
                                                    description="make sure search is finish")
                logging.info("Get search results")
                if asset in first_filter_result.text:
                    logging.info("Filter finish")
                    break
                else:
                    logging.info("Wait for the next search")
                    time.sleep(5)
            else:
                logging.info("No action is found for this floc")
                no_data = True
                break
        except Exception as e:
            logging.error(e)
            pass
    
    if no_data:
        logging.info("No data is found. Click the cancel button")
        find_element_and_click(driver, "//span[contains(text(), 'Cancel')]", by="xpath")
    else:
        # scroll bar 
        scrollbar, clickable = find_element(driver,
                                "//div[@class='add-bulk-actions']//div[@class='dx-scrollable-scrollbar dx-widget dx-scrollbar-horizontal dx-scrollbar-hoverable']//div[@class='dx-scrollable-scroll-content']",
                                by="xpath")
        ActionChains(driver).click_and_hold(scrollbar).move_by_offset(-300, 0).release().perform()


        #  This is to drag the select all button into view
        action_name, _ = find_element(driver,
                                    "//td[@aria-label='Column Action, Filter cell']//input",
                                    by="xpath", description="action name")
        logging.info("find action text area")
        try:
            action_name.send_keys("")
            logging.info("send keys to action text area")
        except:
            raise Exception(f"ERROR[add_job_plan] Could not send keys to action textbox")
        #  This is to drag the select all button into view

        ActionChains(driver).click_and_hold(scrollbar).move_by_offset(-50, 0).release().perform()

        logging.info("Looking for Select All action")
        # click select all action
        find_element_and_click(driver,
                                "//div[@class='add-bulk-actions-container']//tr[@class='dx-row dx-column-lines dx-header-row']//span[@class='dx-checkbox-icon']",
                                by="xpath")
        logging.info("Click select all action button")
                        

        # click Add
        find_element_and_click(driver, "//span[contains(text(), 'Add')]", by="xpath")
        logging.info("Click Add button")

        


def get_created_package_and_job_plan():
    created_package = {}
    with open("created_package.csv", "r") as f:
        for line in f:
            line = line.strip("\n")
            package_id, package_url = line.split(",")
            created_package[package_id] = package_url
    
    created_job_plan = {}
    with open("created_job_plan.csv", "r") as f:
        for line in f:
            line = line.strip("\n")
            package_id, job_plan = line.split(",")
            if package_id not in created_job_plan:
                created_job_plan[package_id] = [job_plan]
            else:
                created_job_plan[package_id].append(job_plan)
    
    linked_asset = {}
    with open("linked_asset.csv", "r") as f:
        for line in f:
            line = line.strip("\n")
            package_id, asset = line.split(",")
            if package_id not in linked_asset:
                linked_asset[package_id] = [asset]
            else:
                linked_asset[package_id].append(asset)


    return created_package, created_job_plan, linked_asset

    

def run_selenium_instance(chrome_driver_path, url_home_page, input_csv_list, run_selenium_headless, username,
                          password):
    unique_package_id_list = input_csv_list['Package ID'].unique().tolist()

    logging.info(f"unique_package_id_list : {unique_package_id_list}")

    package_job_plan_dict = {p: input_csv_list.loc[input_csv_list['Package ID'] == p]['Job Plan ID'].unique().tolist()
                             for p in unique_package_id_list}

    logging.info(f"package_job_plan_dict : {package_job_plan_dict}")

    package_floc_dict = {p: input_csv_list.loc[input_csv_list['Package ID'] == p]['Asset Name'].unique().tolist() for p
                         in unique_package_id_list}
    
    logging.info(f"package_floc_dict : {package_floc_dict}")

    created_package, created_job_plan, linked_asset = get_created_package_and_job_plan()

    logging.info(f"created_package: {created_package}")
    logging.info(f"created_job_plan: {created_job_plan}")
    logging.info(f"linked_asset: {linked_asset}")

    f_created_package = open("created_package.csv", "a")
    f_created_job_plan = open("created_job_plan.csv", "a")
    f_linked_asset = open("linked_asset.csv", "a")

    driver = open_incognito_window(chrome_driver_path, url_home_page, run_selenium_headless)
    driver.implicitly_wait(300)

    log_into_meridium(url_home_page, run_selenium_headless, driver, username, password)

    navigate_to_asi_overview_tab(driver)

    for i, package_id in enumerate(unique_package_id_list):
        logging.info(f"Start processing package {i+1}/{len(unique_package_id_list)} '{package_id}' with {len(package_floc_dict[package_id])} flocs and {len(package_job_plan_dict[package_id])} job plans")
        start_time = time.time()

        
        if package_id not in created_package:
            # click create new package 
            find_element_and_click(driver, "//div[@class='block-group page-filter-tools']//button[contains(text(),'New')]",
                                by="xpath")
            # create new package
            create_new_package(driver, package_id)
            # set the flag
            new_package_created = True
        else:
            logging.info("package created. Jump with url")
            driver.get(created_package[package_id])
            new_package_created = False

        # manage actions using floc
        # click "Manage actions"
        find_element_and_click(driver, "//span[contains(text(),'Manage Actions')]", by="xpath")

        if new_package_created:
            time.sleep(2) # wait for the url to change so that it can be saved in the file correctly
            # write created package id to csv 
            f_created_package.write(f"{package_id},{driver.current_url}\n")
            # record created_package
            created_package[package_id] = driver.current_url
            created_job_plan[package_id] = []
            linked_asset[package_id] = []

        asset_list = package_floc_dict[package_id]
        for j, asset in enumerate(asset_list):
            logging.info(f"Processing {j+1}/{len(asset_list)} flocs: {asset}")
            if package_id in linked_asset.keys():
                if asset in linked_asset[package_id]:
                    logging.info(f"Asset {asset} already linked to package {package_id}. Skip this one")
                    continue
            else:
                linked_asset[package_id] = []

            # -----------------------------
            # this is to skip the asset that has already been added due to substrings
            n_substrings = 0
            for l_a in linked_asset[package_id]:
                if l_a in asset:
                    n_substrings += 1
                    logging.info(F"Asset {asset} has already been added due to substring {l_a}")
                    linked_asset[package_id].append(asset)
                    f_linked_asset.write(f"{package_id},{asset}\n")
                    break
            if n_substrings > 0:
                continue
            # -----------------------------
            else:
                manage_actions_with_floc(driver, asset)  # each package should have at least one floc
                linked_asset[package_id].append(asset)
                f_linked_asset.write(f"{package_id},{asset}\n")
                logging.info(f"Package {package_id} has linked asset {linked_asset[package_id]}")
            
        
        job_plan_list = package_job_plan_dict[package_id]
        for j, job_plan_id in enumerate(job_plan_list):
            logging.info(f"Adding {j+1}/{len(job_plan_list)} job_plan: {job_plan_id}")
            if package_id in created_job_plan.keys():
                if job_plan_id in created_job_plan[package_id]:
                    logging.info(f"Job plan already created. Skip {job_plan_id}")
                    continue
            else:
                created_job_plan[package_id] = []

            # click the plus button
            find_element_and_click(driver,
                                   "//section[@class='expanded active border-right']//mi-more-options-noko//i[@class='icon-plus']",
                                   by="xpath")
            logging.info("Click the plus button")

            # click "Job Plan"
            find_element_and_click(driver,
                                   "//div[@class='more-options-outer-container']//span[contains(text(), 'Job Plan')]",
                                   by="xpath")
            logging.info("Click 'job Plan'")

            job_plan_data = input_csv_list.loc[
                (input_csv_list['Package ID'] == package_id) & (input_csv_list['Job Plan ID'] == job_plan_id)]

            # add new job plan
            add_job_plan(driver, job_plan_data.iloc[0])

            # write created job plan to csv 
            f_created_job_plan.write(f"{package_id},{job_plan_id}\n") 
            # record created job plan
            created_job_plan[package_id].append(job_plan_id)
            logging.info(f"Package {package_id} has job plans {created_job_plan[package_id]}")

            # add actions
            link_actions_to_jobplan(driver, job_plan_data)

            logging.info("Go back to the package tab")
            # Go Back
            find_element_and_click(driver, "//button[@data-action='backInHistory']//i[@class='icon-back-arrow']",
                                   by="xpath")
        
        logging.info("Closing the current package tab")
        
        time.sleep(3) # Account for slow santos system
        close_btn, _ = find_element(driver, f"//li[@title='{package_id}']//i[@class='tab-close ds ds-cross']",by="xpath")
        close_btn.click()
                
        # find_element_and_click(driver, f"//li[@title='{package_id}']//i[@class='tab-close ds ds-cross']",by="xpath")
        
        logging.info(f"Finish processing package '{package_id}' with {len(package_floc_dict[package_id])} flocs and {len(package_job_plan_dict[package_id])} job plans")
        logging.info(f"Finish processing current package in {time.time() - start_time} seconds")




def get_input_csv_list(csv_path_file: str):
    if not os.path.exists(csv_path_file):
        raise Exception(f"ERROR[get_input_csv_list] {csv_path_file} does not exist")

    data = pd.read_csv(csv_path_file, encoding= 'unicode_escape')

    return data


if __name__ == "__main__":
    # Get environmental variables
    username = os.getenv("MERIDIUM_USERNAME")
    password = os.getenv("MERIDIUM_PASSWORD")
    chrome_driver_path = os.getenv("MERIDIUM_CHROME_DRIVER_PATH")
    input_csv_path = os.getenv("MERIDIUM_INPUT_CSV_PATH")

    url_home_page = os.getenv("MERIDIUM_URL_HOME_PAGE")

    input_csv_list = get_input_csv_list(input_csv_path)

    restart_system_error = False

    start_time = time.time()
    run_selenium_headless = False  # must run with display up

    logging.info(f"User Name: \"{username}\"")
    logging.info(f"CSV File Path: {input_csv_path}")
    logging.info(f"ChromeDriver Path: {chrome_driver_path}")

    run_selenium_instance(chrome_driver_path, url_home_page, input_csv_list, run_selenium_headless, username, password)

    logging.info(f"Finished processing {input_csv_path} in {time.time() - start_time} seconds")

    while True:
        time.sleep(1e5) # prevent the browser to be closed automatically. Otherwise the last job plan cannot link actions 
