# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 12:29:09 2018

@author: Peng Wang

Scrape jobs from indeed.ca
"""

import random, json
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time, os
import config
import math

# We only collect max 500 jobs from each city
max_results_per_city = 500
# Number of jobs show on each result page
page_record_limit = 50
#num_pages = int(max_results_per_city/page_record_limit)
#num_pages=2

def get_jobs_info(search_location):
    '''
    Scrape from web or read from saved file
    Input: 
        search_location - search job in a certain city. Input from commond line.
    Output: 
        jobs_info - a list that has info of each job i.e. link, location, title, company, salary, desc
    '''
    exists = os.path.isfile(config.JOBS_INFO_JSON_FILE)
    if exists:
        with open(config.JOBS_INFO_JSON_FILE, 'r') as fp:
            jobs_info = json.load(fp)            
    else:
        jobs_info = web_scrape(search_location)
    return jobs_info
        
def web_scrape(search_location):
    '''
    Scrape jobs from sa.indeed.com
    When scraping web, be kind and patient
    Web scraping 101: http://www.gregreda.com/2013/03/03/web-scraping-101-with-python/
    Input: 
        search_location - search job in a certain city. Input from command line.
    Output: 
        jobs_info - a list that has info of each job i.e. link, location, title, company, salary, desc
    '''
    # urls of all jobs
    #job_links = []
    # Record time for web scraping
    start = time.time() # start time
    # Launch webdriver
    driver = webdriver.Chrome(config.WEBDRIVER_PATH)
    job_locations = config.JOB_LOCATIONS
    # If search location is defined, only search that location
    if (len(search_location) > 0):
        job_locations = [search_location]
        
    # *** Extract all job urls ***
    jobs_info = []
    for location in job_locations: 
        url = 'https://sa.indeed.com/jobs?q='+ config.JOB_SEARCH_WORDS + '&l=' \
        + location + '&limit=' + str(page_record_limit) + '&fromage='+ str(config.DAY_RANGE)
        # Set timeout
        driver.set_page_load_timeout(15)
        webdriver.DesiredCapabilities.CHROME["unexpectedAlertBehaviour"] = "accept"
        driver.get(url)
        # Be kind and don't hit indeed server so hard
        time.sleep(3)
        print("page displayed")
        nb_result=driver.find_element(By.XPATH, '//*[@id="searchCountPages"]')
        time.sleep(5)
        print(nb_result)
        numbers=[int(s) for s in nb_result.text.split() if s.isdigit()]
        print(numbers)
        num_pages=math.ceil((numbers[-1])/15)
        print("number of pages= ", num_pages)
        for i in range(1,num_pages+1):
            try:
                #driver.find_element(By.XPATH, f'//*[@id="resultsCol"]/nav/div/ul/li[{i+1}]/a/span').click()
                #print("OK1")
                jobs_list = driver.find_element(By.XPATH,'//*[@id="mosaic-provider-jobcards"]/ul')
                #print("OK1")
                #ts = ", len(jobs_lists))
                jobs = jobs_list.find_elements(By.CLASS_NAME, f'slider_container')
                time.sleep(5)
                print("lenth of jobs = ", len(jobs))
                # For each job on the page find its url
                for j in range(1,len(jobs)+1):
                    job_each=driver.find_element(By.XPATH, '//*[@id="mosaic-provider-jobcards"]/ul/li['+str(j)+']')
                    try:
                        job_each.click()
                    except WebDriverException:
                        print("Element is not clickable")

                    time.sleep(3)
                    print("I am currently opening a job")
                    #C = driver.find_element(By.CLASS_NAME, 'resultContent')
                    #try:
                        #C.click()
                    #except WebDriverException:
                        #print("Element is not clickable")

                    time.sleep(3)
                    #print(driver.current_url)
                    job_link=driver.current_url
                    time.sleep(3)
                    title = driver.find_element(By.CLASS_NAME, 'jobsearch-JobInfoHeader-title-container').text
                    print(title)
                    time.sleep(3)
                    company = driver.find_element(By.CLASS_NAME,'jobsearch-CompanyInfoContainer').text
                    print(company)
                    time.sleep(3)
                    desc= driver.find_element(By.ID,'jobDescriptionText').text
                    print(desc)

                    print("OK4")
                    #apply_company=driver.find_element(By.ID, f'applyButtonLinkContainer')
                    #apply_company = driver.find_element(By.CLASS_NAME,"icl-u-xs-hide")
                    #d=C.find_element(By.CLASS_NAME,'icl-u-lg-hide')
                    print("OK5")
                    #job_link = apply_company.get_attribute('href')
                    #job_link=driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div/div/div/div[1]/div/div[1]/div[1]/div[4]/div/div[3]/div/div/div[1]/a')
                    #print(job_link)
                    print("OK6")
                    #job_links.append({'location':location, 'job_link':job_link})
                    jobs_info.append({'link': job_link,'location': location, 'title': title, 'company': company,'salary':None,
                        'desc':desc})
                print ('scraping {} page {}'.format(location, i+1))
                # Go next page
                if i<num_pages: driver.find_element(By.CLASS_NAME,'np').click()


                #driver.find_element_by_link_text('Next »').click()
            except NoSuchElementException:
                # If nothing find, we are at the end of all returned results
                print ("{} finished".format(location))
                break        
            # Be kind and don't hit indeed server so hard
            time.sleep(3)
    # Write all jobs links to a json file so it can be reused later
    #with open(config.JOBS_LINKS_JSON_FILE, 'w') as fp:
        #json.dump(job_links, fp)
        
    # ***Go through each job url and gather detailed job info ***
    # Info of all jobs
    '''jobs_info = []
    for job_lk in job_links:
        # Make some random wait time between each page so we don't get banned 
        m = random.randint(5,7)
        time.sleep(m) 
        # Retrieve single job url
        link = job_lk['job_link'] 
        driver.get(link)   
        # Job city and province
        location = job_lk['location']
        # Job title
        title = driver.find_element_by_xpath('//*[@class="icl-u-xs-mb--xs icl-u-xs-mt--none jobsearch-JobInfoHeader-title"]').text
        # Company posted the job
        company = driver.find_element_by_xpath('//*[@class="icl-u-lg-mr--sm icl-u-xs-mr--xs"]').text
        # Salary: if no such info, assign NaN
        if (len(driver.find_elements_by_xpath('//*[@class="jobsearch-JobMetadataHeader-item "]'))==0):
            salary = np.nan 
        else:
            salary = driver.find_element_by_xpath('//*[@class="jobsearch-JobMetadataHeader-item "]').text
        # Job description
        desc = driver.find_element_by_xpath('//*[@class="jobsearch-JobComponent-description icl-u-xs-mt--md"]').text
        jobs_info.append({'link':link, 'location':location, 'title':title, 'company':company, 'salary':salary, 'desc':desc})'''
    # Write all jobs info to a json file so it can be re-used later
    with open(config.JOBS_INFO_JSON_FILE, 'w') as fp:
        json.dump(jobs_info, fp)
    # Close and quit webdriver
    driver.quit()    
    end = time.time() # end time
    # Calculate web scaping time
    scaping_time = (end-start)/60.
    print('Took {0:.2f} minutes scraping {1:d} data scientist/engineer/analyst jobs'.format(scaping_time, len(jobs_info)))
    return jobs_info