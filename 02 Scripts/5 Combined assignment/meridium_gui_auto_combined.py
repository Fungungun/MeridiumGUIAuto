import os
import time
import threading

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
    driver = webdriver.Chrome(chrome_driver_exe,options=options)
    driver.get(url)
    return driver

def find_element(web_driver,value:str,by = "xpath",wait_time_sec=60,description=""):
    # Note 1: Always forgot to put in by, changed it so that it defaults to xpath
    # Note 2: Always forgot to put in // at the front of xpath, added if statement to catch that mistake
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            if by == "id":
                return web_driver.find_element_by_id(value)
            elif by == "xpath":
                if value[:2] != "//":
                    logging.info(f"ERROR[find_element] for {value} using {by} // was not set")
                    break
                return web_driver.find_element_by_xpath(value)
            elif by =="xpath_multi":
                if value[:2] != "//":
                    logging.info(f"ERROR[find_element] for {value} using {by} // was not set")
                    break
                return web_driver.find_elements_by_xpath(value) # will return list
            elif by == "class":
                return web_driver.find_element_by_class_name(value)

            raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")
        except:
            pass
    if by == "":
        raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")

def find_element_and_click(web_driver,value:str,by = "xpath",wait_time_sec=60,description=""):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec:
        try:
            element = find_element(web_driver,value,by=by,wait_time_sec=wait_time_sec)
            element.click()
        except:
            pass
        else:
            return
    raise ElementNotFoundError(f"ERROR[find_element] couldn't find element {description}: {value} using {by} within {wait_time_sec} seconds")
    
def find_elements_search_for_innerhtml(web_driver,xpath:str,innerhtml:str,action="click",wait_time_sec=60,description="",upper_case=False):
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

def find_elements_search_for_innerhtml_then_click(web_driver,xpath:str,innerhtml:str,action="click",wait_time_sec=60,description=""):
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


def log_into_meridium(url,base_path,run_selenium_headless,driver,username,password):
    input_user_id = find_element(driver,"userid",by="id",description="User ID textbox")
    try:
        input_user_id.send_keys(username)
    except:
        raise ElementStale(f"ERROR[log_into_meridium] Could not send keys to User ID textbox")

    input_password = find_element(driver,"password",by="id",description="Password textbox")

    try:
        input_password.send_keys(password)
    except:
        raise ElementStale(f"ERROR[log_into_meridium] Could not send keys to Password textbox")

    find_element_and_click(driver,"//button[@type='submit']",by="xpath")

def navigate_to_asm_overview_tab(driver):
    find_element_and_click(driver,"//div[@title='Strategy']",by="xpath",description="Strategy menu left hand pane") 
    time.sleep(0.5) # Little bit of wait to allow loading of data so it doesn't open it in a new tab
    find_element_and_click(driver,"//a[@href='#/strategy/overview']",by="xpath",description="Drop down strategy overview from strategy menu")

def navigate_to_asm_template(driver,asm_template_name: str,):
    # Note 1: Attempted to use the mi-tile however it did not have a click attribute and would error out
    # Note 2: HTML only spawned when selenium was in focus, TODO check up on this with Cheng
    # Note 3: After coming back to asm template ovierview the previous Template selection still remains in place

    find_element_and_click(driver,"//mi-tile[@text='Templates']",by="xpath",description="Templates box on right hand side")
    time.sleep(0.5)
    find_element_and_click(driver,"//button[@class='btn btn-icon rg-filter']",by="xpath",description="Search icon for asm templates, get this first one in the array")

    search_text_box = find_element(driver,"//td[@aria-label='Column Template ID, Filter cell']//input[@class='dx-texteditor-input']",by="xpath",description="ASM template search textbox")
    try:
        search_text_box.send_keys(asm_template_name)
    except:
        raise ElementStale("ERROR[navigate_to_asm_template] Couldn't send keys to ASM template search textbox")

    time.sleep(1.5) 

    find_elements_search_for_innerhtml(driver,"//td/a",asm_template_name,description=f"Row for template name {asm_template_name}",upper_case=True)

def navigate_to_system_strategy_management(driver,system_id:str):
        find_element_and_click(driver,"//mi-tile[@text='System and Unit Strategies']",by="xpath",description="Templates box on right hand side")
        time.sleep(0.5)
        find_element_and_click(driver,"//button[@class='btn btn-icon rg-filter']",by="xpath",description="Search icon for system and unit strategies")    
        search_text_box_strategy_type = find_element(driver,"//td[contains(@aria-label,'Strategy Type')]//input",by="xpath",description="System and unit strategy search bar that has appeared")
        try:
            search_text_box_strategy_type.send_keys("System")
        except:
            raise ElementStale(f"ERROR[navigate_to_system_strategy_management] Couldn't send keys to Strategy Type to narrow down list to strategies for system |{system_id}|")
        search_text_box_strategy_id = find_element(driver,"//td[contains(@aria-label,'Strategy ID')]//input",by="xpath",description="System and unit strategy search bar that has appeared")
        try:
            search_text_box_strategy_id.send_keys(system_id)
        except:
            raise ElementStale(f"ERROR[navigate_to_system_strategy_management] Couldn't send keys to Strategy ID textbox to find strategy |{system_id}|") 
        find_elements_search_for_innerhtml_then_click(driver,"//td[@aria-colindex='1']/a",system_id,description="System strategy id which is searched for under 'System and Unit Strategies'")

        find_elements_search_for_innerhtml_then_click(driver,"//section[contains(@class,'border-right')]//a","Manage Strategy",description="Manage Strategy which is selected once the strategy has been selected. Under System Strategy Details along with Risk Analysis and Review Strategy")

def find_floc_in_list_click(driver,floc:str,wait_time_sec=60,description=""):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec: # Loop until you can select floc
        try:
            potential_floc_list = find_element(driver,"//td[@aria-colindex='2']",by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper()
                        if floc_innterhtml_uppercase == f"{floc} ".upper(): # Must have space, split removes delimter. Must convert ot upper case 
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
            potential_floc_list = find_element(driver,"//td[@aria-colindex='2']",by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper()
                        if floc_innterhtml_uppercase == f"{floc} ".upper(): # Must have space, split removes delimter. Must convert ot upper case 
                                try:    
                                    potential_floc.find_element_by_xpath(".//a").click()
                                    return
                                except:
                                    pass
        except:
            pass
    raise InnerHTMLNotInElement(f"ERROR[find_floc_in_list_click] for {description}: Couldn't find {floc} in the list")


def apply_template(driver,floc:str,asm_template:str):
    correctly_assigned_asm_to_floc = False

    find_element_and_click(driver,"//button[@title='Apply Template']",by="xpath",description="Apply template") # Apply template
    find_element_and_click(driver,"//button[@class='next btn btn-primary btn-text']",by="xpath",description="Next button") # next button

    asset_family_type_search = find_element(driver,"//input[@class='mi-multi-value-selected-value-text pull-left']",by="xpath",description="Text box to search asset family")
    try:
        asset_family_type_search.clear() # Remove existing asset family type
        asset_family_type_search.send_keys("Functional Locatio") # Filling out "Functional Location" will remove search
    except:
        raise ElementStale(f"ERROR[apply_template] Could not send keys to Text box to search asset family to type in Functional Location")


    find_elements_search_for_innerhtml(driver,"//p","Functional Location",description="Asset family")

    find_elements_search_for_innerhtml(driver,"//button[@class='btn btn-text']","Done",description="asset family done button")

    time.sleep(0.75)

    find_element_and_click(driver,"//*[@id='template-target-grid']//button[@class='btn btn-icon rg-filter']",by="xpath",description="search icon for functional location")

    floc_id_search_bar = find_element(driver,"//*[@id='template-target-grid']//div[@class='dx-datagrid-headers dx-datagrid-nowrap']//td[@aria-label='Column ID, Filter cell']//input",by="xpath",description="functional location search input textbox")
    try:
        floc_id_search_bar.send_keys(floc)
    except:
        raise ElementStale(f"ERROR[apply_template] Could not send keys to functional location search input textbox to type in {floc}")

    find_floc_in_list_click(driver,floc,description="FLOC to click")

    find_element_and_click(driver,"//button[@class='next btn btn-primary btn-text']",by="xpath",description="next button to assign floc")

    selected_template_name = find_element(driver,"//span[@data-bind='text: selectedTemplateName()']",description="selected template name confirmation")
    selected_template_name_innerhtml = selected_template_name.text

    selected_floc = find_element(driver,"//textarea[@class='applytemplatewizardlaststeptextarea']",description="selected floc name confirmation")
    selected_floc_innerhtml = selected_floc.text
    
    if "~" in selected_floc_innerhtml:
        floc_innerhtml_list = selected_floc_innerhtml.split("~")
        if len(floc_innerhtml_list) > 1:
            floc_innerhtml_upper = floc_innerhtml_list[0].upper()
            if not ( floc_innerhtml_upper == f"{floc} ".upper() and selected_template_name_innerhtml.upper() == asm_template.upper() ): # Must have space, split removes delimter
                raise FLOCandASMTemplateNotConfirmed(f"ERROR[apply_template] could not confirm {floc} to {asm_template}")
            
    
    time.sleep(0.25) # Note: click was not working may have been to quick

    find_element_and_click(driver,"//button[@class='finish btn btn-primary btn-text']",by="xpath",description="finish button to apply the template")

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
        logging.info(f"ERROR[break_list_into_chunks] number of chunks should be 1 or greater instead it was {number_of_chunks}")

    length_of_sub_lists = round(len(floc_asm_list)/number_of_chunks)

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
    search_text_box = find_element(driver,"//input[@class='dx-texteditor-input']",by="xpath",description="asset strategy search textbox, search for the floc which has recently been assigned a asm template, always get first element")
    try:
        search_text_box.send_keys(floc_name)

    except:
        raise ElementStale("ERROR[navigate_to_asm_template] Couldn't send keys to ASM template search textbox")
    # find_elements_search_for_innerhtml(driver,"//td/a",floc_name,description=f"Get asset strategy {floc_name} after clicking search icon and sending keys to search box",upper_case=True)
    find_floc_in_list_click_hyperlink(driver, floc_name)
    check_if_strategy_draft_or_modified_and_activate(driver)

def link_floc_strategy_to_system(driver,system_id:str,floc:str):
    find_element_and_click(driver,"//button[@title='Add Existing']",description="Add or the + icon next to the search binoculars. Used to add a strategy once it has been determined that it is not already added")
    find_element_and_click(driver,"//mi-resultgrid[@id='asm-add-existing-strategy-grid']//i[@class='icon-search']",description="Binoculars to search for floc strategies to add to the system")

    search_box_floc_strategy_to_assign_to_system = find_element(driver,"//div[@class='asm-add-existing-strategy']//td[@aria-colindex='2']//input",description="Text search box to find floc strategy to link to system")
    try:
        search_box_floc_strategy_to_assign_to_system.send_keys(floc)
    except:
        raise ElementStale(f"ERROR[link_floc_strategy_to_system] Couldn't send keys to system |{system_id}| to find floc |{floc}|") 
    find_floc_in_list_click(driver,"//div[@class='asm-add-existing-strategy']//div[contains(@class,'dx-datagrid-rowsview')]//td[@aria-colindex='2']",floc,description=f"Find the potential list of floc to activate in the list of Add Existing Asset Strategies. For floc {floc}")
    find_elements_search_for_innerhtml_then_click(driver,"//button[contains(@data-bind,'addExistingStrategies')]","Add",description=f"Add button, adds new asset or floc |{floc}| strategy to the system |{system_id}|")   

def is_floc_already_assigned_to_system(driver,floc:str,wait_time_sec=15,description=""):
    start_time = time.time()
    while time.time() - start_time < wait_time_sec: # Loop until you can select floc
        try:
            potential_floc_list = find_element(driver,"//td[@aria-colindex='2']/a",by="xpath_multi")
            for potential_floc in potential_floc_list:
                potential_floc_innerhtml = potential_floc.text
                if "~" in potential_floc_innerhtml:
                    floc_innerhtml_list = potential_floc_innerhtml.split("~")
                    if len(floc_innerhtml_list) > 1:
                        floc_innterhtml_uppercase = floc_innerhtml_list[0].upper()
                        if floc_innterhtml_uppercase == f"{floc} ".upper(): # Must have space, split removes delimter. Must convert ot upper case 
                            return True
        except:
            pass
    return False

def see_if_floc_has_already_been_assigned_to_system(driver,floc:str):
    find_element_and_click(driver,"//button[@title='Search'][contains(@class,'rg-filter')]",description="Search button to check that strategy has not already been assigned")
    search_box_possible_already_assigned_strategy = find_element(driver,"//td[contains(@aria-label,'Column Strategy')]//input",description="Strategy input box that drops down when you click the search goggle icon under manage strategy")
    try:
        search_box_possible_already_assigned_strategy.send_keys(floc)
    except:
        raise ElementStale(f"ERROR[run_selenium_instance] Couldn't send keys to strategy with the floc |{floc}| under system") 
    return is_floc_already_assigned_to_system(driver, floc)

def close_strategy_tab(driver,strategy_id:str):
    find_element_and_click(driver,f"//li[@title='{strategy_id}']/i",description=f"The close button for the system strategy which has been opened, |{strategy_id}|")

def run_selenium_instance(chrome_driver_path,url_home_page,base_path,floc_asm_list,run_selenium_headless,thread_num,username,password):
    global error_log
    start_time = 0
    login_required = True

    for row_index,row in enumerate(floc_asm_list):
        floc_name = row[0]
        asm_template_name = row[1]
        system_id = row[2]

        if start_time == 0: # time logging for user interest
            logging.info(f"Thread[{thread_num}] starts processing FLOC |{floc_name}| ASM |{asm_template_name}| SYSTEM |{system_id}|. [{row_index} of {len(floc_asm_list)} ~ %{round(row_index/len(floc_asm_list)*100,1)} complete]")
        else:
            logging.info(f"Thread[{thread_num}] starts processing FLOC |{floc_name}| ASM |{asm_template_name}| SYSTEM |{system_id}|. [{row_index} of {len(floc_asm_list)} ~ %{round(row_index/len(floc_asm_list)*100,1)} complete] prior lap took {round(time.time()-start_time,2)} seconds")
        start_time = time.time()

        if login_required:
            logging.info(f"Thread[{thread_num}] Opening incognito window")
            driver = open_incognito_window(chrome_driver_path,url_home_page,run_selenium_headless)

        finished_steps = 0

        try: # Error handling
            if login_required == True:
                logging.info(f"Thread[{thread_num}] Logging into meridium")
                log_into_meridium(url_home_page,base_path,run_selenium_headless,driver,username,password)
                login_required = False

            logging.info(f"Thread[{thread_num}] Step 1: ASM Template -> FLOC Starts")
            logging.info(f"Thread[{thread_num}] Navigating to ASM Overview tab")
            navigate_to_asm_overview_tab(driver) # step 1, ASM Template -> FLOC
            logging.info(f"Thread[{thread_num}] Navigating to ASM Template tab")
            navigate_to_asm_template(driver,asm_template_name) # step 1, ASM Template -> FLOC
            logging.info(f"Thread[{thread_num}] Applying Template")
            apply_template(driver,floc_name,asm_template_name) # step 1 FINISHED YAY!
            logging.info(f"Thread[{thread_num}] Closing assigned ASM Template tab")
            close_assigned_asm_template_tab(driver,asm_template_name) # Close tab should be on ASM overivew tab now
            logging.info(f"Thread[{thread_num}] Closing ASM Overview tab")
            close_asm_overview_tab(driver)

            finished_steps = 1

            logging.info(f"Thread[{thread_num}] Step 2: Activate FLOC Strategy Starts")
            logging.info(f"Thread[{thread_num}] Navigating to ASM Overview tab")
            navigate_to_asm_overview_tab(driver) # step 2, activate floc strategy
            logging.info(f"Thread[{thread_num}] Activating FLOC strategy")
            activate_floc_strategy(driver,floc_name) # Step 2 activation
            logging.info(f"Thread[{thread_num}] Closing Asset Strategy")
            close_asset_strategy(driver,floc_name) #End of step 2
            logging.info(f"Thread[{thread_num}] Closing ASM Overview tab")
            close_asm_overview_tab(driver)

            finished_steps = 2

            logging.info(f"Thread[{thread_num}] Step 3: Asset Strategy -> System Starts")
            logging.info(f"Thread[{thread_num}] Navigating to ASM Overview tab")
            navigate_to_asm_overview_tab(driver) # step 3, Asset Strategy -> System
            logging.info(f"Thread[{thread_num}] Navigating to System Strategy Management")
            navigate_to_system_strategy_management(driver,system_id)
            if see_if_floc_has_already_been_assigned_to_system(driver,floc_name) == False:
                logging.info(f"Thread[{thread_num}] Linking FLOC strategy to system")
                link_floc_strategy_to_system(driver,system_id,floc_name)
                logging.info(f"Thread[{thread_num}] Closing Strategy tab")
                close_strategy_tab(driver,system_id)
                logging.info(f"Thread[{thread_num}] Closing ASM Overview tab")
                close_asm_overview_tab(driver)
                logging.info(f"Thread[{thread_num}] Navigating to ASM Overview tab")
                navigate_to_asm_overview_tab(driver)
                logging.info(f"Thread[{thread_num}] FLOC |{floc_name}| assigned to |{system_id}|")
            else:
                logging.info(f"Thread[{thread_num}] Closing Strategy tab")
                close_strategy_tab(driver,system_id)
                logging.info(f"Thread[{thread_num}] Closing ASM Overview tab")
                close_asm_overview_tab(driver)
                logging.info(f"Thread[{thread_num}] Navigating to ASM Overview tab")
                navigate_to_asm_overview_tab(driver)
                logging.info(f"Thread[{thread_num}] System |{system_id}| has already been assigned |{floc_name}|, no assignment was carried  out.")

            finished_steps = 3
            
        except (ElementStale,ElementNotFoundError,InnerHTMLNotInElement) as e: 
            if finished_steps == 0:
                err_msg = f"Thread[{thread_num}] Error raised in STEP 1: ASM Template {asm_template_name} -> FLOC {floc_name}"
            elif finished_steps == 1:
                err_msg = f"Thread[{thread_num}] Error raised in STEP 2: Activate FLOC Strategy {floc_name}"
            elif finished_steps == 2:
                err_msg = f"Thread[{thread_num}] Error raised in STEP 3: Asset Strategy {floc_name} -> System {system_id}"
            else:
                err_msg = f"Thread[{thread_num}] Unknown error. Raise to alex."
            error_log.append(err_msg)
            login_required = True
            driver.quit()
        else:
            pass


def write_error_log(error_log,start_time,error_log_path:str,number_of_browsers_to_run_in_parallel:int,username:str,asm_to_floc_link_csv_path:str):
    
    with open(error_log_path, 'a') as fileobj:
        print(f"User Name,\"{username}\"",file=fileobj)
        print(f"Start time,{time.ctime(start_time)}",file=fileobj)
        print(f"End time,{time.ctime(time.time())}",file=fileobj)
        print(f"Time Taken [s],{time.time()-start_time}",file=fileobj)
        print(f"Number of processes run in parallel ,{number_of_browsers_to_run_in_parallel}",file=fileobj)
        print(f"CSV File Path,{asm_to_floc_link_csv_path}",file=fileobj)
        print("",file=fileobj)
        # print("FLOC not assigned,Corresponding ASM Template not assigned",file=fileobj)
        for error in error_log:
            print(error,file=fileobj)
        print("",file=fileobj)
    

if __name__ == "__main__": 
    # TODO 1: Logging
    # TODO 2: Config, version control
    # TODO 3: Public repo only https://www.gitkraken.com/git-client otherwise classic github

    start_time = time.time()
    # --- User variables to change ----
    base_path = "C:/Users/chenghuanliu/Desktop/Projects/MeridiumGUIAuto/"
    username = os.getenv("MERIDIUM_USERNAME")
    password = os.getenv("MERIDIUM_PASSWORD")

    # --- program variables ---
    chrome_driver_path = f"{base_path}/02 Scripts/chromedriver.exe"
    # asm_to_floc_link_csv_path = f"{base_path}/04 CSV/2 Assign ASM Template To FLOC/floc that didnt work for kecheng.csv"
    asm_to_floc_link_csv_path = f"{base_path}/04 CSV/5 Combined CSV upload/4800-SAT Upload Test.csv"
    error_log_path = f"{base_path}/04 CSV/5 Combined CSV upload/error_log.csv"
    url_home_page = "https:\\meridium.nexusic.com\meridium\#2;rte=home;rte=assets\hierarchy\-1;rte=\strategy\overview;"
    run_selenium_headless = False # must run with display up
    number_of_browsers_to_run_in_parallel = 1
    error_log = []

    if os.path.exists(base_path) == False:
        raise FileExistsError(f"ERROR[MAIN] The base file path of {base_path} does not exist")

    floc_asm_list = get_asm_and_floc_assignment_from_csv(asm_to_floc_link_csv_path)

    broken_up_floc_asm_list = list(break_list_into_chunks(floc_asm_list,number_of_browsers_to_run_in_parallel))

    # run_selenium_instance(chrome_driver_path,url_home_page,base_path,broken_up_floc_asm_list[0],run_selenium_headless,0,username,password)

    logging.info(f"User Name: \"{username}\"")
    logging.info(f"Start time: {time.ctime(start_time)}")
    logging.info(f"Number of processes run in parallel: {number_of_browsers_to_run_in_parallel}")
    logging.info(f"CSV File Path: {asm_to_floc_link_csv_path}")
    logging.info(f"ChromeDriver Path: {chrome_driver_path}")
    logging.info(f"Total number of rows to process: {len(floc_asm_list)}")

    # Threading, read only action
    threads = []

    for thread_num,partial_floc_asm_list in enumerate(broken_up_floc_asm_list):
        x = threading.Thread(target=run_selenium_instance, args=(chrome_driver_path,url_home_page,base_path,partial_floc_asm_list,run_selenium_headless,thread_num,username,password))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

    # write err log
    write_error_log(error_log,start_time,error_log_path,number_of_browsers_to_run_in_parallel,username,asm_to_floc_link_csv_path)
    

    logging.info(f"Finished in {round(time.time()-start_time,1)}")



    