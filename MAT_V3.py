import os
import time
import threading
import random

from selenium import webdriver # Selenium tools
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import random
import time
import requests

import logging
import csv 

from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(handlers=[logging.FileHandler('meridium_gui_auto.log'), logging.StreamHandler()],
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
logging.info('-----------------------------------New Session-------------------------------------')



# Error handling
class CSVWrongHeaders(Exception):
    pass
class ElementNotFoundError(Exception):
    pass

class ElementStale(Exception):
    pass

class InnerHTMLNotInElement(Exception):
    pass

class FLOCandASMTemplateNotConfirmed(Exception):
    pass
class OtherStateID(Exception):
    pass


def open_incognito_window(chrome_driver_exe,url,run_selenium_headless):   
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("start-maximized")
    if run_selenium_headless == True:
        options.add_argument('headless')
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(chrome_driver_exe,options=options)
    # driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver

def find_element(web_driver,value:str,by = "xpath",wait_time_sec=90,description="",sleep_time=0):
    # Note 1: Always forgot to put in by, changed it so that it defaults to xpath
    # Note 2: Always forgot to put in // at the front of xpath, added if statement to catch that mistake
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
            elif by =="xpath_multi":
                if value[:2] != "//":
                    logging.error(f"ERROR[find_element] for {value} using {by} // was not set")
                    break
                return web_driver.find_elements_by_xpath(value) # will return list
            elif by == "class":
                return web_driver.find_element_by_class_name(value)

            raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")
        except:
            pass

        if sleep_time != 0:
            time.sleep(sleep_time)
    if by == "":
        raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")

def find_element_and_click(web_driver,value:str,by = "xpath",wait_time_sec=120,description="",sleep_time=0):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            element = find_element(web_driver,value,by=by,wait_time_sec=wait_time_sec)
            element.click()
        except:
            pass
        else:
            return

        if sleep_time != 0:
            time.sleep(sleep_time)
    raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")
    
def find_elements_search_for_innerhtml(web_driver,xpath:str,innerhtml:str,action="click",wait_time_sec=120,description="",upper_case=False):
    # Note 1: Sometimes when searching for innerhtml the document changes and so innerhtml raises an error hence a try except statement is needed
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            elements_list = find_element(web_driver,xpath,by="xpath_multi",wait_time_sec=2) # Assume that the list will be short enough to load without typing anything
            for element in elements_list:
                if upper_case == True:
                    if element.text.upper() == innerhtml.upper(): # Case insensitive
                        if action == "click":
                            element.click()
                            return
                else:
                    if element.text == innerhtml: # Case insensitive
                        if action == "click":
                            element.click()
                            return
        except:
            pass
    raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {xpath} using with innerHTML of {innerhtml} within {wait_time_sec} seconds")

def find_elements_search_for_innerhtml_then_click(web_driver,xpath:str,innerhtml:str,action="click",wait_time_sec=120,description=""):
    # Note 1: Sometimes when searching for innerhtml the document changes and so innerhtml raises an error hence a try except statement is needed
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            elements_list = find_element(web_driver,xpath,by="xpath_multi",wait_time_sec=2) # Assume that the list will be short enough to load without typing anything
            for element in elements_list:
                if element.text == innerhtml:
                    if action == "click":
                        element.click()
                        return
        except:
            pass
    raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {xpath} using with innerHTML of {innerhtml} within {wait_time_sec} seconds. Description of element = {description}")


def log_into_meridium(url,run_selenium_headless,driver,username,password):
    
    input_user_id = find_element(driver,"userid",by="id",description="User ID textbox",wait_time_sec=150,sleep_time=1)
    try:
        input_user_id.send_keys(username)
    except:
        raise ElementStale(f"ERROR[log_into_meridium] Could not send keys to User ID textbox")

    time.sleep(1) # Account for slow santos system
    input_password = find_element(driver,"password",by="id",description="Password textbox")

    try:
        input_password.send_keys(password)
    except:
        raise ElementStale(f"ERROR[log_into_meridium] Could not send keys to Password textbox")

    find_elements_search_for_innerhtml_then_click(driver,"//select[@tabindex=3]/option","APMPROD",description="Selecting APMPROD, server which all information is stored") 

    find_element_and_click(driver,"//button[@type='submit']",by="xpath")

def navigate_to_asm_overview_tab(driver):
    find_element_and_click(driver,"//div[@title='Strategy']",by="xpath",description="Strategy menu left hand pane",wait_time_sec=150) 
    time.sleep(0.5) # Little bit of wait to allow loading of data so it doesn't open it in a new tab
    find_element_and_click(driver,"//a[@href='#/strategy/overview']",by="xpath",description="Drop down strategy overview from strategy menu")

def navigate_to_asm_template(driver,asm_template_name: str,):
    # Note 1: Attempted to use the mi-tile however it did not have a click attribute and would error out
    # Note 2: HTML only spawned when selenium was in focus, TODO check up on this with Cheng
    # Note 3: After coming back to asm template ovierview the previous Template selection still remains in place

    find_element_and_click(driver,"//mi-tile[@text='Templates']",by="xpath",description="Templates box on right hand side. Sometimes ths lags",sleep_time=3)
    time.sleep(0.5)
    find_element_and_click(driver,"//button[@class='btn btn-icon rg-filter']",by="xpath",description="Search icon for asm templates, get this first one in the array")

    time.sleep(1) # Account for slow santos system
    search_text_box = find_element(driver,"//td[@aria-label='Column Template ID, Filter cell']//input[@class='dx-texteditor-input']",by="xpath",description="ASM template search textbox")
    try:
        search_text_box.send_keys(asm_template_name)
    except:
        raise ElementStale("ERROR[navigate_to_asm_template] Couldn't send keys to ASM template search textbox")

    # Account for asm template not existing inside of Meridium
    wait_until_data_had_loaded(driver,asm_template_name)
    if is_there_no_data_for_asm_search(driver,asm_template_name) == True:
        raise ElementNotFoundError(f"ERROR[navigate_to_asm_template] asm template does not exist in meridium")
    try:
        find_elements_search_for_innerhtml(driver,"//td/a",asm_template_name,description=f"Row for template name {asm_template_name}",upper_case=True)
    except:
        raise ElementNotFoundError(f"ERROR[navigate_to_asm_template] asm template does not exist in meridium")

def navigate_to_system_strategy_management(driver,system_id:str):
    # Saw mistake where information was double typed
    find_element_and_click(driver,"//mi-tile[@text='System and Unit Strategies']",by="xpath",description="Templates box on right hand side",sleep_time=3)
    time.sleep(1)
    find_element_and_click(driver,"//button[@class='btn btn-icon rg-filter']",by="xpath",description="Search icon for system and unit strategies")    

    time.sleep(1) # Account for slow santos system
    search_text_box_strategy_id = find_element(driver,"//td[contains(@aria-label,'Strategy ID')]//input",by="xpath",description="System and unit strategy search bar that has appeared",wait_time_sec=10)
    
    time.sleep(1) #account for slow santos system
    try:
        search_text_box_strategy_id.send_keys(system_id)
    except:
        raise ElementStale(f"ERROR[navigate_to_system_strategy_management] Couldn't send keys to Strategy ID textbox to find strategy |{system_id}|") 

    # Account for system not existing inside of Meridium
    wait_until_data_had_loaded(driver,system_id)
    if is_there_no_data_for_system_search(driver,system_id) == True:
        raise ElementNotFoundError(f"ERROR[navigate_to_system_strategy_management] system does not exist in meridium")
    try:
        find_elements_search_for_innerhtml_then_click(driver,"//td[@aria-colindex='1']/a",system_id,description="System strategy id which is searched for under 'System and Unit Strategies'",wait_time_sec=15)
    except:
        raise ElementNotFoundError(f"ERROR[navigate_to_system_strategy_management] system does not exist in meridium")

    find_elements_search_for_innerhtml_then_click(driver,"//section[contains(@class,'border-right')]//a","Manage Strategy",description="Manage Strategy which is selected once the strategy has been selected. Under System Strategy Details along with Risk Analysis and Review Strategy")

def find_floc_in_list_click(driver,floc:str,xpath="//td[@aria-colindex='2']",wait_time_sec=60,description=""):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec: # Loop until you can select floc
        try:
            time.sleep(2)
            potential_floc_list = find_element(driver,xpath,by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper().strip(" ") # End used to be .upper()
                        if floc_innterhtml_uppercase == floc.upper(): # End used to be .upper() Must have space, split removes delimter. Must convert ot upper case 
                                try:    
                                    potential_floc.click()
                                    return
                                except:
                                    pass
        except:
            pass
    raise InnerHTMLNotInElement(f"ERROR[find_floc_in_list_click] for {description}: Couldn't find {floc} in the list")

def find_floc_in_list_click_hyperlink(driver,floc:str,wait_time_sec=60,description=""):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec: # Loop until you can select floc
        try:
            time.sleep(2)
            potential_floc_list = find_element(driver,"//td[@aria-colindex='2']/a",by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper().strip(" ")
                        if floc_innterhtml_uppercase == floc.upper(): # End used to be .upper() Must have space, split removes delimter. Must convert ot upper case 
                            try:
                                potential_floc.click()
                                return
                            except:
                                pass
        except:
            pass
    raise InnerHTMLNotInElement(f"ERROR[find_floc_in_list_click] for {description}: Couldn't find {floc} in the list")

def wait_until_data_had_loaded(driver,floc:str,wait_time_sec=120):
    # Note 1: Santos system has long wait time, wait until the data has loaded
    start_time = time.time()
    while time.time() - start_time < wait_time_sec: 
        spinner_element = find_element(driver,"//div[@class='dx-overlay dx-widget dx-visibility-change-handler dx-loadpanel']",wait_time_sec=3,description="Finding the loading spinner to see when data has loade")
        if spinner_element == None:
            print(f"took {round(time.time()-start_time,2)} sec to load locations")
            return
    raise ElementStale(f"Couldn't load locations for {floc}, waited for {round(time.time()-start_time,2)} seconds")

def is_there_no_data(driver,floc:str,wait_time_sec=60):
    no_data_element = find_element(driver,"//span[@class='dx-datagrid-nodata']",by="xpath",wait_time_sec=2,description=f"for {floc} seeing if there was No Data found")
    if no_data_element == None:
        return False
    else:
        return True

def is_there_no_data_selection_of_existing_asset_strategy(driver,floc:str,wait_time_sec=60):
    # Note 1: Other section picked up scenario where No Data was for asset strategies assigned to the system
    no_data_element = find_element(driver,"//section[@class='content existing-strategy-dialog']//span[@class='dx-datagrid-nodata']",by="xpath",wait_time_sec=2,description=f"for {floc} seeing if there was No Data found")
    if no_data_element == None:
        return False
    else:
        return True

def is_there_no_data_for_asm_search(driver,asm_template:str,wait_time_sec=60):
    # Note 1: Other section picked up scenario where No Data was for asset strategies assigned to the system
    no_data_element = find_element(driver,"//mi-resultgrid[contains(@data,'Asset Templates')]//span[@class='dx-datagrid-nodata']",by="xpath",wait_time_sec=2,description=f"for {asm_template} checking if it exsits by looking for No Data found")
    if no_data_element == None:
        return False
    else:
        return True

def is_there_no_data_for_system_search(driver,system_id:str,wait_time_sec=60):
    # Note 1: Other section picked up scenario where No Data was for asset strategies assigned to the system
    no_data_element = find_element(driver,"//mi-resultgrid[contains(@data,'System And Unit Strategies')]//span[@class='dx-datagrid-nodata']",by="xpath",wait_time_sec=2,description=f"for {system_id} checking if it exsits by looking for No Data found")
    if no_data_element == None:
        return False
    else:
        return True
        
def is_apply_template_button_clickable(driver):
    apply_template_button = find_element(driver,"//button[@title='Apply Template']",by="xpath",description="Find apply template button to check if it is disabled")

    if apply_template_button == None: # Account for nothing returning
        return False
    try:
        if apply_template_button.get_attribute("disabled") == None:
            return True
        return False
    except:
        return True

def apply_template(driver,floc:str,asm_template:str,wait_time_sec=60):
    # Note 1: Sometimes santos system is slow, must wait until the strategy template has been assigned and activated
    # Can take a long time, assumed to be 10 minutes max
    time.sleep(3) # Account for slow santos system
    start_time = time.time()
    while time.time() - start_time < wait_time_sec and is_apply_template_button_clickable(driver) == False:
        time.sleep(2)
     

    find_element_and_click(driver,"//button[@title='Apply Template']",by="xpath",description="Apply template") # Apply template
    find_elements_search_for_innerhtml(driver,"//span[@class='radio-text']","Apply the template as a master",description="Apply template as a master, instead of the original copy")
    find_element_and_click(driver,"//button[@class='next btn btn-primary btn-text']",by="xpath",description="Next button") # next button

    time.sleep(1) # Account for slow santos system
    asset_family_type_search = find_element(driver,"//input[@class='mi-multi-value-selected-value-text pull-left']",by="xpath",description="Text box to search asset family")
    try:
        asset_family_type_search.clear() # Remove existing asset family type
        asset_family_type_search.send_keys("Locations") # Filling out "Functional Location" will remove search
    except:
        raise ElementStale(f"ERROR[apply_template] Could not send keys to Text box to search asset family to type in Locations")

    find_elements_search_for_innerhtml(driver,"//p","Locations",description="Asset family, want to select Locations plural")

    find_elements_search_for_innerhtml(driver,"//button[@class='btn btn-text']","Done",description="asset family done button")
    
    wait_until_data_had_loaded(driver,floc) # Account for slow santos system

    find_element_and_click(driver,"//*[@id='template-target-grid']//button[@class='btn btn-icon rg-filter']",wait_time_sec=150,by="xpath",description="search icon for location (FLOC), Santos Meridium system appears to hang here.")

    time.sleep(1) # Account for slow santos system
    floc_id_search_bar = find_element(driver,"//*[@id='template-target-grid']//div[@class='dx-datagrid-headers dx-datagrid-nowrap']//td[@aria-label='Column ID, Filter cell']//input",by="xpath",description="Locations (FLOC) search input textbox")
    try:
        floc_id_search_bar.send_keys(floc)
    except:
        raise ElementStale(f"ERROR[apply_template] Could not send keys to functional location search input textbox to type in {floc}")
    
    wait_until_data_had_loaded(driver,floc) # Account for slow santos system
    if is_there_no_data(driver,floc):
        find_element_and_click(driver,"//span[contains(@class,'close-dialog')]",description="Close button of apply template once there is no floc listed in strategy")
        return False
    try: # Sometimes FLOC is a subset of others hence data will be displayed
        find_floc_in_list_click(driver,floc,wait_time_sec=5,description="Locations or FLOC to click that is being linked to the ASM Template. Santos system runs slow as there are lots of FLOCs")
    except:
        find_element_and_click(driver,"//span[contains(@class,'close-dialog')]",description="Close button of apply template once there is no floc listed in strategy")
        return False
    
    find_element_and_click(driver,"//button[@class='next btn btn-primary btn-text']",by="xpath",description="next button to assign floc")

    time.sleep(1) # Note: click was not working may have been to quick

    find_element_and_click(driver,"//button[@class='finish btn btn-primary btn-text']",by="xpath",description="finish button to apply the template")

    return True

def get_asm_and_floc_assignment_from_csv(csv_path_file:str):
    if os.path.exists(csv_path_file) == False:
        raise FileExistsError(f"ERROR[get_asm_and_floc_assignment_from_csv] file path {csv_path_file} does not exist")
    
    file_obj = open(csv_path_file,"r")
    data_lines = file_obj.readlines()
    file_obj.close()

    ret_list = []

    for row,line in enumerate(data_lines):
        line = line.strip("\n")
        columns = line.split(",")
        if row == 0: # first row
            floc_header = columns[0]
            asm_header = columns[1]
            system_header = columns[2]
            if floc_header.upper() != "FLOC" or asm_header.upper() != "ASM" or system_header.upper() != "SYSTEM":
                raise CSVWrongHeaders(f"ERROR[get_asm_and_floc_assignment_from_csv] csv file headers should be |FLOC|ASM|SYSTEM| instead it was |{floc_header}|{asm_header}|{system_header}|")
        else:
            floc = columns[0]
            asm = columns[1]
            system = columns[2]
            ret_list.append([floc,asm,system])
    return ret_list


def close_assigned_asm_template_tab(driver,asm_template_name):
    li_elements = find_element(driver,"//li",by="xpath_multi",description="List of li elements for asm template tab")
    for element in li_elements:
        possible_title = element.get_attribute("title")
        if possible_title.upper() == asm_template_name.upper():    
            find_element_and_click(driver,f"//li[@title='{possible_title}']/i",by="xpath",description=f"close_assigned_asm_template_tab for {asm_template_name}")
            break

def close_asm_overview_tab(driver):
    return find_element_and_click(driver,f"//li[@title='ASM Overview']/i",by="xpath",description='close_asm_overview_tab')

def break_list_into_chunks(lst,number_of_chunks:int):
    if number_of_chunks < 1: 
        logging.error(f"ERROR[break_list_into_chunks] number of chunks should be 1 or greater instead it was {number_of_chunks}")

    length_of_sub_lists = round(len(lst)/number_of_chunks)

    for i in range(0,len(lst),length_of_sub_lists):
        yield lst[i:i+length_of_sub_lists]

def check_if_strategy_draft_or_modified_and_activate(driver):
    # Note 1: Sometimes script moves to quickly and it cannot get the text from the active state button. Added while loop to counter that lag in load time
    state = ""
    start_time = time.time()
    while state == "" and time.time() - start_time < 60:
        active_state_button = find_element(driver,"//div[@id='asm-toolbar']//section[@class='mi-state-trans-container']//span[@data-bind='text: activeState']",description="active state button, used to determine what text it is which will decide if it is a draft or modified strategy")
        state = active_state_button.text
        

    find_element_and_click(driver,"//div[@id='asm-toolbar']//section[@class='mi-state-trans-container']//button",description=f"Active state buttton, was {state}")
    if state == "Draft": # Help with debugging
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-transition']//li","Baseline",description="Baseline under strategy")
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-assignment block-group']//button","Done",description="done button to propose baseline")
        find_elements_search_for_innerhtml_then_click(driver,"//div[contains(@class,'two-buttons')]","Yes",description="Yes button to confirm draft")
    elif state == "Modified":
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-transition']//li","Propose",description="Propose under modified from drop down manage state assignment")
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-assignment block-group']//button","Done",description=f"done button to propose changes from Modified")
        find_elements_search_for_innerhtml_then_click(driver,"//div[contains(@class,'two-buttons')]","Yes",description="Yes button to confirm proposed modifications")
        find_element_and_click(driver,"//div[contains(@class,'clearfix')]/button[contains(@class,'text-edit-save')]",description="OK button to confirm basis for revision data")
        time.sleep(1.5)
        find_element_and_click(driver,"//div[@id='asm-toolbar']//section[@class='mi-state-trans-container']//button",description=f"Select Pending Review to then select Make Active")
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-transition']//li","Make Active",description="Select Make active when it drops down from Pending Review")
        find_elements_search_for_innerhtml_then_click(driver,"//div[@class='state-assignment block-group']//button","Done",description=f"done button to propose changes from Modified")
        find_elements_search_for_innerhtml_then_click(driver,"//div[contains(@class,'two-button')]","Yes",description=f"Yes button for strategy approval. The dialog box that appears once you have moved on from Pending Review")
    elif state == "Active":
        pass
    elif state == "":
        raise OtherStateID("ERROR[check_if_strategy_draft_or_modified_and_activate]: Could not find a value for the state button which is normally draft, modified or active. Skip")
    else:
        raise OtherStateID("ERROR[check_if_strategy_draft_or_modified_and_activate] Clicked on a FLOC Strategy Template that was not Draft or Modified. Raise to alex")

    start_time = time.time()
    while time.time() - start_time < 60: 
        activation_state = find_element(driver,"//span[@class='active-state']",description="Activation status is green or orange. Usually says Draft, Modified or Active").get_attribute("innerHTML")
        if activation_state == "Active":
            return
    raise FLOCandASMTemplateNotConfirmed("ERROR[check_if_strategy_draft_or_modified_and_activate] Managed to click all the buttons to activate the floc strategy template however could not find activation within 60 seconds")

def close_asset_strategy(driver,floc_name:str):
     find_element_and_click(driver,f"//li[contains(@title,'{floc_name}')]/i",description=f"The close button for the system strategy which has been opened, |{floc_name}|")
    

def activate_floc_strategy(driver,floc_name:str):
    find_element_and_click(driver,"//mi-tile[@title='Asset Strategies']",description="Asset Strategies tile on the ASM template page")
    find_element_and_click(driver,"//button[@class='btn btn-icon rg-filter']",by="xpath",description="Search icon for asset strategies, get this first one in the array")

    time.sleep(1) # Account for slow santos system
    search_text_box = find_element(driver,"//input[@class='dx-texteditor-input']",by="xpath",description="asset strategy search textbox, search for the floc which has recently been assigned a asm template, always get first element")
    try:
        search_text_box.send_keys(floc_name)

    except:
        raise ElementStale("ERROR[navigate_to_asm_template] Couldn't send keys to ASM template search textbox")
    # find_elements_search_for_innerhtml(driver,"//td/a",floc_name,description=f"Get asset strategy {floc_name} after clicking search icon and sending keys to search box",upper_case=True)
    find_floc_in_list_click_hyperlink(driver, floc_name)
    check_if_strategy_draft_or_modified_and_activate(driver)

def link_floc_strategy_to_system(driver,system_id:str,floc:str,wait_time_sec=120):
    # Note 1: Took time for system to activate FLOC strategy, will need to wait until it is found, takes approx 15 seconds extra
    start_time = time.time()
    while time.time()-start_time < wait_time_sec:
        time.sleep(2)
        find_element_and_click(driver,"//button[@title='Add Existing']",description="Add or the + icon next to the search binoculars. Used to add a strategy once it has been determined that it is not already added")
        time.sleep(2)
        find_element_and_click(driver,"//mi-resultgrid[@id='asm-add-existing-strategy-grid']//i[@class='icon-search']",description="Binoculars to search for floc strategies to add to the system")

        time.sleep(1) # Account for slow santos system
        search_box_floc_strategy_to_assign_to_system = find_element(driver,"//div[@class='asm-add-existing-strategy']//td[@aria-colindex='2']//input",description="Text search box to find floc strategy to link to system")
        try:
            search_box_floc_strategy_to_assign_to_system.send_keys(floc)
        except:
            raise ElementStale(f"ERROR[link_floc_strategy_to_system] Couldn't send keys to system |{system_id}| to find floc |{floc}|")

        wait_until_data_had_loaded(driver,floc) # Account for slow santos system
        if is_there_no_data_selection_of_existing_asset_strategy(driver,floc) == True:
            find_element_and_click(driver,"//button[contains(@data-bind,'click: cancel')][@class='btn btn-text btn-secondary']",description="Cancel button for when the FLOC has not been assigned a strategy so No Data occurs when assigning FLOC strategy to system")
        else:
            break

    find_floc_in_list_click(driver,floc,description=f"Find the potential list of FLOC strategyies to link to systems in the list of Add Existing Asset Strategies. For floc {floc}",wait_time_sec=30)
    find_elements_search_for_innerhtml_then_click(driver,"//button[contains(@data-bind,'addExistingStrategies')]","Add",description=f"Add button, Links new asset or floc |{floc}| strategy to the system |{system_id}|")   

def is_floc_already_assigned_to_system(driver,floc:str,wait_time_sec=15,description=""):
    if is_there_no_data(driver,floc): # If no data then there is no floc assigned
        return False

    start_time = time.time()
    while time.time() - start_time < wait_time_sec: # Loop until you can select floc
        try:
            potential_floc_list = find_element(driver,"//td[@aria-colindex='2']/a",by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper().strip(" ") # Always space at end of FLOC
                        if floc_innterhtml_uppercase == floc.upper(): #Split removes delimter. Must convert ot upper case 
                            return True
        except:
            pass
    return False

def see_if_floc_has_already_been_assigned_to_system(driver,floc:str,wait_time_sec=20):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        time.sleep(2)
        # Note 1: In some cases the search icon was not pressed, hence it would not be able to see an input box to send keys
        find_element_and_click(driver,"//button[@title='Search'][contains(@class,'rg-filter')]",description="Search button to check that strategy has not already been assigned")

        search_box_possible_already_assigned_strategy = find_element(driver,"//td[contains(@aria-label,'Column Strategy')]//input",wait_time_sec=2,description="Strategy input box that drops down when you click the search goggle icon under manage strategy")
        try:
            search_box_possible_already_assigned_strategy.send_keys(floc)
            break
        except:
            pass
            #raise ElementStale(f"ERROR[run_selenium_instance] Couldn't send keys to strategy with the floc |{floc}| under system") 

    wait_until_data_had_loaded(driver,floc) # Account for slow santos system

    return is_floc_already_assigned_to_system(driver, floc,description="Loop through list of FLOC strategies assigned to system, see if one matches FLOC")

def close_strategy_tab(driver,strategy_id:str):
    find_element_and_click(driver,f"//li[@title='{strategy_id}']/i",description=f"The close button for the system strategy which has been opened, |{strategy_id}|")

def run_selenium_instance(chrome_driver_path,url_home_page,floc_asm_list,run_selenium_headless,thread_num,username,password,steps_to_include):
    global error_log
    start_time = 0
    login_required = True

    for row_index,row in enumerate(floc_asm_list):
        floc_name = row[0]
        asm_template_name = row[1]
        system_id = row[2]

        logging.info(f"Thread[{thread_num}] FLOC |{floc_name}| ASM |{asm_template_name}| SYSTEM |{system_id}| ")
        logging.info(f"Thread[{thread_num}] [{row_index} of {len(floc_asm_list)} ~ %{round(row_index/len(floc_asm_list)*100,1)} complete] ")
        if start_time != 0:
            logging.info(f"Thread[{thread_num}] Prior lap took {round(time.time()-start_time,2)} seconds ")

        start_time = time.time()

        if login_required:
            driver = open_incognito_window(chrome_driver_path,url_home_page,run_selenium_headless)
        finished_steps = 0

        try: # Error handling
            if login_required == True:
                log_into_meridium(url_home_page,run_selenium_headless,driver,username,password)
                login_required = False

            if "1" in steps_to_include:
                navigate_to_asm_overview_tab(driver) # step 1, ASM Template -> FLOC
                navigate_to_asm_template(driver,asm_template_name) # step 1, ASM Template -> FLOC
                was_template_successfuly_applied =  apply_template(driver,floc_name,asm_template_name) # step 1 FINISHED YAY!
                close_assigned_asm_template_tab(driver,asm_template_name) # Close tab should be on ASM overivew tab now
                close_asm_overview_tab(driver)

            finished_steps = 1
        
            finished_steps = 2 # Not needed anymore, was the activation step

            if "3" in steps_to_include:
                navigate_to_asm_overview_tab(driver) # step 3, Asset Strategy -> System
                navigate_to_system_strategy_management(driver,system_id)
                if see_if_floc_has_already_been_assigned_to_system(driver,floc_name) == False:
                    link_floc_strategy_to_system(driver,system_id,floc_name)
                    close_strategy_tab(driver,system_id)
                    close_asm_overview_tab(driver)
                    navigate_to_asm_overview_tab(driver)
                else:
                    close_strategy_tab(driver,system_id)
                    close_asm_overview_tab(driver)
                    logging.debug(f"Thread[{thread_num}] Navigating to ASM Overview tab")
                    navigate_to_asm_overview_tab(driver)
                    logging.debug(f"Thread[{thread_num}] System |{system_id}| has already been assigned |{floc_name}|, no assignment was carried  out.")

            finished_steps = 3
            logging.info(f"Thread[{thread_num}] Finished successfully |{floc_name}| |{asm_template_name}| |{system_id}|")
        except (ElementStale,ElementNotFoundError,InnerHTMLNotInElement) as e: 
            if finished_steps == 0:
                err_msg = f"Thread[{thread_num}] STEP 1: ASM Template {asm_template_name} -> FLOC {floc_name}. {e}"
                csv_err_msg = f"STEP 1: ASM -> FLOC,{floc_name},{asm_template_name},{system_id},{e}"
            elif finished_steps == 1:
                err_msg = f"Thread[{thread_num}] STEP 2: Activate FLOC Strategy {floc_name}. {e}"
                csv_err_msg = f"STEP 2: ACTIVATION,{floc_name},{asm_template_name},{system_id},{e}"
            elif finished_steps == 2:
                err_msg = f"Thread[{thread_num}] STEP 3: Asset Strategy {floc_name} -> System {system_id}. {e}"
                csv_err_msg = f"STEP 3: FLOC -> SYSTEM,{floc_name},{asm_template_name},{system_id},{e}"
            else:
                err_msg = f"Thread[{thread_num}] Unknown error Raise to alex. {e}"
                csv_err_msg = f"-1,{floc_name},{asm_template_name},{system_id}, {e}"

            logging.error(err_msg)
            error_log.append(csv_err_msg)
            login_required = True
            driver.quit()
        else:
            pass

def write_error_log(error_log,start_time,error_log_path:str,number_of_browsers_to_run_in_parallel:int,username:str,asm_to_floc_link_csv_path:str):
    
    with open(error_log_path, 'a+') as fileobj:
        print(f"User Name,\"{username}\"",file=fileobj)
        print(f"Start time,{time.ctime(start_time)}",file=fileobj)
        print(f"End time,{time.ctime(time.time())}",file=fileobj)
        print(f"Time Taken [s],{time.time()-start_time}",file=fileobj)
        print(f"Number of processes run in parallel ,{number_of_browsers_to_run_in_parallel}",file=fileobj)
        print(f"CSV File Path,{asm_to_floc_link_csv_path}",file=fileobj)
        print("",file=fileobj)

        print("STEP_FAILED,FLOC,ASM,SYSTEM,ERROR",file=fileobj)
        for error in error_log:
            print(error,file=fileobj)
        print("",file=fileobj)

def aggregate_count_rows_of_asm_template_list(asm_template_list):
    unique_asm_template = set(asm_template_list)

    asm_template_count = []
    for asm_template in unique_asm_template:
        count = asm_template_list.count(asm_template)
        asm_template_count.append([asm_template,count])
    return asm_template_count

def random_solver_allocate_asm_to_thread(asm_template_list,asm_template_count,number_of_threads:int,solve_time_sec=10):
    target_row_per_thread = len(asm_template_list)/number_of_threads
    asm_assignment_new = []
    asm_assignment_old = []
    difference_new = [0]*number_of_threads
    difference_old = [0]*number_of_threads
    start_time = time.time()
    first_run = True
    while time.time() - start_time < solve_time_sec:
        difference_new = [0]*number_of_threads
        for row in asm_template_count:
            asm_template = row[0]
            count = row[1]
            assignment_num = random.randint(1,number_of_threads)
            difference_new[assignment_num-1] = difference_new[assignment_num-1]+count
            asm_assignment_new.append([asm_template,count,assignment_num])

        for thread,rows_per_thread in enumerate(difference_new):
            rows_per_thread = abs(rows_per_thread - target_row_per_thread)
            difference_new[thread] = rows_per_thread

        if first_run == True:
            asm_assignment_old = asm_assignment_new.copy()
            difference_old = difference_new.copy()
            first_run = False
        else:
            if sum(difference_new) < sum(difference_old):
                asm_assignment_old = asm_assignment_new.copy()
                difference_old = difference_new.copy()

    return_asm_template = []
    for asm_template in asm_assignment_old:
        return_asm_template.append([asm_template[0],asm_template[2]])
    return return_asm_template

def return_thread_from_asm_assignment(asm:str,asm_template_assignment):
    # Assume that floc is unique
    for row in asm_template_assignment:
        if asm in row:
            thread_num = row[1]
            return thread_num

def split_upload_file_into_threads_unique_asm_templates(floc_asm_sys_list,number_of_threads:int):
    # Note 1: Can't have multiple threads accessing the asm template at the same time.
    if number_of_threads > 1:
        # Aggregate to ASM Template
        asm_template_list = [x[1] for x in floc_asm_sys_list]

        asm_template_count = aggregate_count_rows_of_asm_template_list(asm_template_list)

        asm_template_assignment = random_solver_allocate_asm_to_thread(asm_template_list,asm_template_count,number_of_threads)
        
        split_list = [None]*number_of_threads
        for row in floc_asm_sys_list:
            asm_in_row = row[1]
            thread_num =  return_thread_from_asm_assignment(asm_in_row,asm_template_assignment)
            if split_list[thread_num-1] == None:
                split_list[thread_num-1] = [row]
            else:
                split_list[thread_num-1].append(row)

        return split_list
    else:
        return_list_one_thread = []
        return_list_one_thread.append(floc_asm_sys_list)
        return return_list_one_thread

def get_previously_errored_rows():
    global error_log
    previous_errored_rows = []
    for error in error_log:
        error_split_comma = error.split(",")
        floc = error_split_comma[1]
        asm = error_split_comma[1]
        system = error_split_comma[1]
        previous_errored_rows.append([floc,asm,system])
    return previous_errored_rows

def comparitor_sort_second_element(list_element):
    return list_element[1]

def sort_lists_by_asm_template(broken_up_floc_asm_list):
    # Pass by reference
    for floc_asm_list in broken_up_floc_asm_list:
        floc_asm_list.sort(key=comparitor_sort_second_element)

def run_selenium_instance_multi_asm_floc_link(chrome_driver_path,url_home_page,floc_asm_list,run_selenium_headless,thread_num,username,password,steps_to_include):
    pass

if __name__ == "__main__": 
    
    # Get environmental variables
    username = os.getenv("MERIDIUM_USERNAME")
    password = os.getenv("MERIDIUM_PASSWORD")
    chrome_driver_path = os.getenv("MERIDIUM_CHROME_DRIVER_PATH")
    asm_to_floc_link_csv_path = os.getenv("MERIDIUM_INPUT_CSV_PATH")
    error_log_path = os.getenv("MERIDIUM_ERROR_LOG_PATH")
    url_home_page = os.getenv("MERIDIUM_URL_HOME_PAGE")
    number_of_browsers_to_run_in_parallel = int(os.getenv("MERIDIUM_NUM_RUN_IN_PARALLEL"))
    steps_to_include = os.getenv("STEPS_TO_INCLUDE")

    error_log = []
    restart_system_error = False
    for run_index in range(3): # Repeat x times and try and upload errors again

        start_time = time.time()
        run_selenium_headless = False  # must run with display up



        if run_index == 0: # Read input file
            floc_asm_list = get_asm_and_floc_assignment_from_csv(asm_to_floc_link_csv_path)
        else: 
            if restart_system_error == False:
                floc_asm_list = get_previously_errored_rows()
                if len(floc_asm_list) == 0:
                    break
                error_log = []

        if restart_system_error == False:
            broken_up_floc_asm_list = split_upload_file_into_threads_unique_asm_templates(floc_asm_list,number_of_browsers_to_run_in_parallel)
        else:
            restart_system_error = True
            for thread_floc_asm_list in broken_up_floc_asm_list:
                index_to_remove_up_to = 0
                for row_index,row in enumerate(thread_floc_asm_list):
                    if error_log[1] == row[0]:
                        index_to_remove_up_to = row_index
                del thread_floc_asm_list[:index_to_remove_up_to]

        broken_up_floc_asm_list = list(filter(None, broken_up_floc_asm_list))
        sort_lists_by_asm_template(broken_up_floc_asm_list)

        logging.info(f"User Name: \"{username}\"")
        logging.info(f"Start time: {time.ctime(start_time)}")
        logging.info(f"Number of processes run in parallel: {number_of_browsers_to_run_in_parallel}")
        logging.info(f"CSV File Path: {asm_to_floc_link_csv_path}")
        logging.info(f"ChromeDriver Path: {chrome_driver_path}")
        logging.info(f"Total number of rows to process: {len(floc_asm_list)}")

        try:
            # Threading, read only action
            threads = []

            for thread_num,partial_floc_asm_list in enumerate(broken_up_floc_asm_list):
                x = threading.Thread(target=run_selenium_instance, args=(chrome_driver_path,url_home_page,partial_floc_asm_list,run_selenium_headless,thread_num,username,password,steps_to_include))
                threads.append(x)
                x.start()
                time.sleep(45) # Stagger start times, to prevent system lag

            for thread in threads:
                thread.join()
        except:
            restart_system_error = True

        # write err log
        write_error_log(error_log,start_time,error_log_path,number_of_browsers_to_run_in_parallel,username,asm_to_floc_link_csv_path)
        

        logging.info(f"Finished in {round(time.time()-start_time,1)}")


    