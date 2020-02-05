import os, platform
import json
import logging
import random
import re

import urllib
import urllib.request
import socket
import urllib.error

import psutil
import requests
import imghdr
import datetime

import operator
import threading

from uuid import uuid4, UUID
from random import randint, choice
from time import sleep
from threading import Thread, active_count
from typing import Dict
from datetime import datetime, timedelta
#from datetime import timedelta
#from bs4 import BeautifulSoup

from django.db.models import Count, F, Value
from django.apps import apps

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.by import By

from user_agent import generate_user_agent
from django.utils import timezone
from walker_panel.models import *
from scripts.common_functions import *
from scripts.sql_querys import *

logger = logging.getLogger('bot')

SCREENSHOTS_DIR = './screenshots/'
CAPTCHAS_DIR = './captchas/'
YANDEX_URL = 'http://yandex.ru'
base_url = 'http://rucaptcha.com'
req_url = base_url + '/in.php'
res_url = base_url + '/res.php'
load_url = base_url + '/load.php'
year = datetime.today().strftime("%Y")
month = datetime.today().strftime("%m")
day = datetime.today().strftime("%d")
SCREENSHOTS_DIR_today = SCREENSHOTS_DIR + year + "." + month + "." + day + "/"

stngs = Setting.objects.get(id=2)
hour_start = stngs.workers_time_start
hour_end = stngs.workers_time_end
api_key = stngs.rucaptcha_key
email_admin = stngs.email_admin
email_dev = stngs.email_dev
enable_log_run = stngs.enable_log_run
enable_log_stalk = stngs.enable_log_stalk
enable_log_proxy = stngs.enable_log_proxy

thread_data = threading.local()

if check_dev():
    email_titel = 'Site Walker DEV'
else:
    email_titel = 'Site Walker'

def log(user: User, task: GroupTask, action: str, level: str = 'info', extra: dict = None, uid: UUID = None):
    log_entry = GroupLog(owner=user, task=task, action=action, extra=json.dumps(extra), level=level, uid=uid)
    log_entry.save()
    logger.info("Task " + str(task.id) + ": " + action)

def get_random_screen_resolution() -> str:
    resolutions = ['1280,768',
                   '1280,800',
                   '1280,1024',
                   '1360,768',
                   '1366,768',
                   '1440,900',
                   '1536,864',
                   '1600,900',
                   '1680,1050',
                   '1920,1080',
                   '1920,1200',
                   '2560,1080',
                   '2560,1440']
    return random.choice(resolutions)

def do_delay(delay: str = 'normal'):
    if delay == 'fast':
        sleep(randint(1, 5))
    elif delay == 'normal':
        sleep(randint(5, 15))
    elif delay == 'slow':
        sleep(randint(15, 30))
    else:
        sleep(randint(1, 30))

def letter_by_letter(task_name: str, by_type: str, by_identifier: str, word: str, driver: Chrome, press_enter: bool):
    if by_type == "xpath":
        element = driver.find_element_by_xpath(by_identifier)
    if by_type == "id":
        element = driver.find_element_by_id(by_identifier)
    if by_type == "class":
        element = driver.find_element_by_class_name(by_identifier)
    element.clear()
    for letter in enumerate(word):
        log_stalk(task_name + " БУКВА ЗА БУКВОЙ letter=" + letter[1], enable_log_stalk)
        element.send_keys(letter[1])
    sleep(3)
    if press_enter:
        element.send_keys(Keys.ENTER)

def trunc_url(url: str) -> str:
    url = re.sub(r'https?://', '', url)
    url = url.replace('www.', '')
    return re.sub(r'/.*', '', url)

def is_same_site(url1: str, url2: str) -> bool:
    url1 = trunc_url(url1)
    url2 = trunc_url(url2)
    return url1 == url2

def is_competitor_site(url, competitor_sites):
    competitor_urls = competitor_sites.split('\r\n')
    for site in competitor_urls:
        if is_same_site(url, site):
            return True
    return False

def save_png(path: str, name: str, url: str):
    file = path + name + ".png"
    urllib.request.urlretrieve(url, file)

def check_file_ext(file: str) -> Dict[bytes, str]:
    with open(file, 'rb') as f:
        raw_data = f.read()
    file_ext = imghdr.what(None, h=raw_data)
    #Dict = [raw_data, file_ext]
    dct = dict(A1 = raw_data, A2 = file_ext)
    return dct

def check_request_response(req: str, task_name: str, file_ext: str, raw_data: bytes) -> str:
    if req[:2] == 'OK':
        captcha_id = req[3:]
        ci_zero_balance(False)
    elif 'ERROR_ZERO_BALANCE' in req:
        ci_zero_balance(True)
        log_stalk(task_name + " На вашем счету недостаточно средств. rucaptcha.com ", enable_log_stalk)
        send_email(email_admin, "RUCAPCHA", email_titel, f" На вашем счету недостаточно средств. rucaptcha.com ")
        send_email(email_dev, "RUCAPCHA", email_titel, f" На вашем счету недостаточно средств. rucaptcha.com ")
        captcha_id = "EMPTY"
    else:
        log_stalk(task_name + " ЗАПРОС отправлен не успешно " + str(req), enable_log_stalk)
        ci_zero_balance(False)
        i = 0
        while req[:2] != 'OK':
            i += 1
            sleep(8)
            log_stalk(task_name + " ЗАПРОС отправлен не успешно " + str(i) + '_' + str(req), enable_log_stalk)
            req = requests.post(req_url, {'key': api_key, 'method': 'post'}, files={'file': ('captcha.' + file_ext, raw_data)}).text
        captcha_id = req[3:]
    return captcha_id

def check_result_response(res: str, task_name: str, captcha_id: str) -> str:
    if res[:2] == 'OK':
        res_input = res[3:]
    elif 'CAPCHA_NOT_READY' in res:
        log_stalk(task_name + " ОТВЕТ получен не успешно CAPCHA_NOT_READY " + res, enable_log_stalk)
        i = 0
        while 'CAPCHA_NOT_READY' in res:
            log_stalk(task_name + " RESULT CAPCHA_NOT_READY : " + str(i) + '_' + res, enable_log_stalk)
            i += 1
            sleep(15)
            res = requests.post(res_url, {'key': api_key, 'action': 'get', 'id': captcha_id}).text
        res_input = res[3:]
    else:
        sleep(15)
        log_stalk(task_name + " ОТВЕТ получен не успешно ELSE " + str(res), enable_log_stalk)
        res = requests.post(res_url, {'key': api_key, 'action': 'get', 'id': captcha_id}).text
        log_stalk(task_name + " RESULT ELSE : " + str(res), enable_log_stalk)
        res_input = res[3:]
    return res_input

"""
def walk_on_site(driver: Chrome, task_name: str):
    for i in range(randint(5, 15)):
        try:
            links = driver.find_elements_by_tag_name('a')
            if check_dev():
                aaa = "ССЫЛКИ: "
                for li in links:
                    aa = li.get_attribute('href')
                    aaa = aaa + ", " + aa
                log_stalk(task_name + "WALK: TITLE Яндекс: " + aaa, enable_log_stalk)
            action = ActionChains(driver)
            link = choice(links)
            save_screenshots(SCREENSHOTS_DIR, "-walk_on_site-", " link = choice", driver)
            action.move_to_element(link)
            action.perform()
            save_screenshots(SCREENSHOTS_DIR, "-walk_on_site-", " action perform", driver)
            do_delay('fast')
            link.click()
            sleep(1)
            save_screenshots(SCREENSHOTS_DIR, "-walk_on_site-", " link click", driver)

            driver.find_element_by_tag_name('body').send_keys(Keys.ESCAPE)
            save_screenshots(SCREENSHOTS_DIR, "-walk_on_site-", " Keys ESCAPE", driver)
            do_delay('fast')

            for y in range(randint(5, 40)):
                try:
                    random_div = choice(driver.find_elements_by_tag_name('div'))
                    action.move_to_element(random_div)
                    save_screenshots(SCREENSHOTS_DIR, "-walk_on_site-", " move_to_element random_div", driver)
                    action.perform()
                    do_delay('fast')
                    driver.execute_script(f"window.scrollTo(0, {randint(1, 500)});")
                except:
                    pass
            sleep(1)
        except Exception as e:
            print(e)
"""

def walk_on_site(driver: Chrome, task_name: str):
    for i in range(randint(5, 15)):
        try:
            links = driver.find_elements_by_tag_name('a')
            action = ActionChains(driver)
            link = choice(links)
            action.move_to_element(link)
            action.perform()
            do_delay('fast')
            link.click()
            sleep(1)
            #driver.save_screenshot(SCREENSHOTS_DIR + "--------------------------------------555-1.png")
            driver.find_element_by_tag_name('body').send_keys(Keys.ESCAPE)
            #driver.save_screenshot(SCREENSHOTS_DIR + "--------------------------------------555-2.png")
            do_delay('fast')

            for y in range(randint(5, 40)):
                try:
                    random_div = choice(driver.find_elements_by_tag_name('div'))
                    action.move_to_element(random_div)
                    action.perform()
                    do_delay('fast')
                    driver.execute_script(f"window.scrollTo(0, {randint(1, 500)});")
                except:
                    pass
            sleep(1)
        except Exception as e:
            print(e)

def input_captcha(res_input: str, task_name: str, taskname: str, driver: Chrome, path: str):
    res_input = res_input.strip()
    log_stalk(task_name + " ВВОДИМ В КАПЧУ>" + str(res_input) + "<", enable_log_stalk)
    captcha_input = driver.find_element_by_id('rep')
    captcha_input.clear()
    captcha_input.send_keys(res_input)
    sleep(5)
    driver.save_screenshot(path + taskname + " END RESULT 1 " + ".png")
    # captcha_input.send_keys(Keys.ENTER)
    driver.find_element_by_class_name('form__submit').click()
    driver.save_screenshot(path + taskname + " END RESULT 2 " + ".png")

def free_captcha(task_name: str, where: str, driver: Chrome):
    #commoninfo = CommonInfo.objects.all()[0]
    commoninfo = CommonInfo.objects.get(id=1)
    if not commoninfo.zero_balance:
        if 'Ой!' in driver.title:
            i = 0
            while 'Ой!' in driver.title:
                i += 1
                if i >= 2:
                    # отправляем жалобу на решение капчи
                    res_bad = requests.post(res_url, {'key': api_key, 'action': 'reportbad', 'id': captcha_id}).text
                    if res_bad[:2] != 'OK':
                        log_stalk(task_name + " ПЕРЕДИДУЩАЯ КАПЧА НЕ ПОДОШЛА - bad репорт отправлен " + str(i), enable_log_stalk)

                taskname = (task_name[5:]).replace(": ", "") + '-^-' + str(i)
                log_stalk(task_name + " ОЙ перед " + where + " !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! " + str(i) + "_Разрешение капчи", enable_log_stalk)

                save_screenshots(CAPTCHAS_DIR, taskname, " СОХРАНЯЕМ КАПЧУ на hdd", driver)
                try:
                    log_stalk(task_name + " GET КАПЧА src ", enable_log_stalk)
                    #captcha_src = driver.find_elements_by_class_name('form__captcha')[0].get_attribute('src')
                    captcha_src = driver.find_elements_by_class_name('captcha_image')[0].get_attribute('src')
                except Exception as e:
                    print(e)
                    log_stalk(task_name + " GET КАПЧА src " + str(e), enable_log_stalk)
                save_png(CAPTCHAS_DIR, taskname, captcha_src)


                file = CAPTCHAS_DIR + taskname + ".png"
                #'''
                #If path was provided, load file.
                if type(file) == str:
                    with open(file, 'rb') as f:
                        raw_data = f.read()
                else:
                    raw_data = file.read()
                #Detect image format.
                file_ext = imghdr.what(None, h=raw_data)
                #'''

                #dct = check_file_ext(file)
                #raw_data = dct[A1]
                #file_ext = dct[A2]

                text = requests.post(req_url, {'key': api_key, 'method': 'post'}, files={'file': ('captcha.' + file_ext, raw_data)}).text
                driver.save_screenshot(CAPTCHAS_DIR + taskname + " BEGIN " + ".png")

                sleep(2)
                captcha_id = check_request_response(text, task_name, file_ext, raw_data)
                log_stalk(task_name + " captcha_id >" + captcha_id + "<", enable_log_stalk)
                sleep(15)
                response = requests.post(res_url, {'key': api_key, 'action': 'get', 'id': captcha_id}).text
                log_stalk(task_name + " RESPONSE : " + str(response), enable_log_stalk)

                res_input = check_result_response(response, task_name, captcha_id)
                log_stalk(task_name + " res_input >" + res_input + "<", enable_log_stalk)

                sleep(5)
                input_captcha(res_input, task_name, taskname, driver, CAPTCHAS_DIR)

                sleep(15)
            ci_task_capched()
            log_stalk(task_name + " КАПЧЕД + 1 " + where + " !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! " + str(i) + "_Разрешена КАПЧА", enable_log_stalk)
        #else:
        #    ci_task_capched()
    else:
        log_stalk(task_name + " На вашем счету недостаточно средств. rucaptcha.com ", enable_log_stalk)
        #send_email(email_admin, "RUCAPCHA", email_titel, f" На вашем счету недостаточно средств. rucaptcha.com ")
        send_email(email_dev, "RUCAPCHA", email_titel, f" На вашем счету недостаточно средств. rucaptcha.com ")

def proc_uptime():
    try:
        f = open("/proc/uptime")
        contents = f.read().split()
        f.close()
    except:
        return "Cannot open uptime file: /proc/uptime"
    total_seconds = float(contents[0])
    return total_seconds

def uptime_obj():
    return Uptime()

class Uptime:
    def __init__(self):
        self.days = int(proc_uptime() / DAY)
        self.hours = int((proc_uptime() % DAY) / HOUR)
        self.minutes = int((proc_uptime() % HOUR) / MINUTE)
        self.seconds = int(proc_uptime() % MINUTE)

class TaskRunner(Thread):
    def __init__(self, task: GroupTask):
        Thread.__init__(self)
        self.task = task
        self.uid = uuid4()
    def run(self):
        task_name = f"Task {self.task.id}(     ): "
        task_city = Group.objects.get(group_name=self.task.target_group)
        tcity = str(task_city.city)
        target_group = Group.objects.get(group_name=self.task.target_group)
        pl = str(target_group.proxy_list)
        logger.info(task_name + "ПРОКСИ ЛИСТ - " + pl)
        check_free_ram(task_name, 400, "СТАРТ ЗАДАЧИ", enable_log_run)
        GroupTask.objects.filter(id=self.task.id).update(running_today=F('running_today') + 1)
        GroupTask.objects.filter(id=self.task.id).update(last_start=timezone.now())
        self.task.refresh_from_db()
        try:
            log(user=self.task.owner, task=self.task, action='TASK_ACTIVATED', uid=self.uid)
            browser_configuration = self.generate_browser_configuration(pl, task_name, self.task.id)
            driver = get_driver(browser_configuration)
            pid = driver.service.process.pid
            self.task.refresh_from_db()
            usedproxy_add_addr(str(self.task.id), thread_data.proxy, str(pid), threading.currentThread().getName())
            self.stalk_sites_in_yandex(driver, browser_configuration, str(pid))
            ci_task_finished()
        except Exception as e:
            logger.exception(task_name + 'Stalking did catch exception ')
            up = UsedProxy.objects.get(address=browser_configuration['proxy'])
            error_save(task_name, thread_data.proxy, tcity, up.template_div, browser_configuration['user-agent'], thread_data.change_region, e)
            log(user=self.task.owner, task=self.task, action='CRASHED', uid=self.uid, extra={'message': f'Прокси {thread_data.proxy} '})
            usedproxy_remove_addr(thread_data.proxy)
            ci_task_crashed()
            if not check_dev():
                send_email(email_admin, "Task CRASHED", email_titel, f"{task_name} \n Task CRASHED \n {thread_data.proxy} \n {tcity} \n {e} ")
            send_email(email_dev, "Task CRASHED", email_titel, f"{task_name} \n Task CRASHED \n {thread_data.proxy} \n {tcity} \n {e} ")
        finally:
            log_stalk(task_name + " ***** THREAD value: " + str(thread_data.proxy), enable_log_stalk)
            log(user=self.task.owner, task=self.task, action='FINISH', uid=self.uid, extra={'message': f'Task finish {thread_data.proxy} '})
            usedproxy_remove_addr(thread_data.proxy)
            driver.quit()
            ci_reboot_reset()
            ci_task_finish()

    def stalk_sites_in_yandex(self, driver: Chrome, proxy_addr: dict, pid: str):
        task_name = f"Task {str(self.task.id)}({pid}): "
        target_grp = Group.objects.get(group_name=self.task.target_group)
        tcity = str(target_grp.city)
        ttarget_url = str(target_grp.target_url)
        tcompetitor_sites = str(target_grp.competitor_sites)
        if target_grp.competitor_sites is None:
            tcompetitor_sites_len = 0
        else:
            tcompetitor_sites_len = len(target_grp.competitor_sites)
        number_competitor_visit = randint(2, 5)
        driver.get(YANDEX_URL)
        sleep(6)
        log_stalk(task_name + "TITLE: " + driver.title, enable_log_stalk)

        if tcity != '':
            self.change_region(driver, task_name, tcity)

        free_captcha(task_name, 'перед send keys - search_query', driver)
        driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "0_SEARCH_QUERY***.png")

        #driver.find_element_by_id('text').send_keys(self.task.search_query, Keys.ENTER)
        try:
            """
            while not "нашлось" in driver.title:
                letter_by_letter(f"{task_name}ПОИСКОВЫЙ ЗАПРОС:", "id", "text", self.task.search_query, driver, False)
                driver.send_keys(Keys.ENTER)
                sleep(5)
                log_stalk(task_name + "нашлось Title: " + driver.title, enable_log_stalk)
                sleep(2)
            """
            letter_by_letter(f"{task_name}ПОИСКОВЫЙ ЗАПРОС:", "id", "text", self.task.search_query, driver, False)
            driver.send_keys(Keys.ENTER)
            sleep(5)
        except Exception as e:
            print(e)
        sleep(8)
        driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "1_SEARCH_QUERY.png")

        log_stalk(task_name + "Title: " + driver.title, enable_log_stalk)
        log_stalk(task_name + "Город: " + tcity, enable_log_stalk)
        log_stalk(task_name + "Целевой сайт: " + ttarget_url, enable_log_stalk)
        log_stalk(task_name + "Сайты конкурентов, кол-во: " + str(tcompetitor_sites_len), enable_log_stalk)
        log_stalk(task_name + "Сайты конкурентов: " + tcompetitor_sites, enable_log_stalk)
        log_stalk(task_name + "Количество заходов к конкурентам: " + str(number_competitor_visit), enable_log_stalk)
        exitFlag = False
        not_done_flag = True

        for current_page in range(stngs.stalker_page_range):
            sleep(5)
            #result_items = driver.find_elements_by_class_name('serp-item')
            free_captcha(task_name, 'перед li serp-item', driver)
            result_items = driver.find_elements_by_xpath("//li[@class='serp-item']")
            sleep(5)

            if len(result_items) == 0:
                #send_email(email_dev, "result_items", email_titel, f" result_items LI = 0 ")
                name = task_name + "_" + str(current_page)
                save_screenshots(SCREENSHOTS_DIR_today, name, " CURRENT PAGE", driver)

                #log_stalk(task_name + "!!! ШАБЛОН DIV !!!", enable_log_stalk)
                #result_items = driver.find_elements_by_xpath("//div[@class='serp-item']")
                #LAST
                #result_items = driver.find_elements_by_xpath("//div[contains(@class, 'serp-item')]")
                #20.05.2019
                #result_items = driver.find_elements_by_xpath("//div[@class='serp-list']/div[contains(@class, 'serp-item')]")
                free_captcha(task_name, 'перед div serp-item', driver)
                result_items = driver.find_elements_by_xpath( "//div[@class='serp-list']/div[@class='serp-item']")
                #result_items = driver.find_elements_by_class_name('serp-item')
                usedproxy_updt_div(proxy_addr['proxy'], True)

                log_stalk(task_name + " - " + str(len(result_items)) + " - " + " Количество serp-item в DIV CLASS ", enable_log_stalk)

            log_stalk(task_name + str(current_page) + " " + line_double, enable_log_stalk)
            log_stalk(task_name + "serp-item КОЛИЧЕСТВО: " + str(len(result_items)), enable_log_stalk)
            #log_stalk(task_name + "template_div: " + str(self.task.template_div), enable_log_stalk)
            up = UsedProxy.objects.get(address=proxy_addr['proxy'])
            log_stalk(task_name + "template_div: " + str(up.template_div), enable_log_stalk)

            for item in result_items:
                log_stalk(task_name + line_short, enable_log_stalk)
                current_position = item.get_attribute('data-cid')
                log_stalk(task_name + "Current_position: " + str(current_position), enable_log_stalk)
                try:
                    hyperlink = item.find_element_by_tag_name('h2')
                except Exception as e:
                    log_stalk(task_name + " не получилось взять ГИПЕРЛИНК  ЛИНКС: " + str(e) + "_", enable_log_stalk)
                    name = task_name + "_" + str(current_page)
                    save_screenshots(SCREENSHOTS_DIR_today, name, " не получилось взять ГИПЕРЛИНК  ЛИНКС", driver)
                    continue
                try:
                    #if self.task.template_div:
                    if up.template_div:
                        #item_text = item.text
                        #item__attribute_href = item.get_attribute('href')
                        #log_stalk(task_name + "item_text: " + str(item_text), enable_log_stalk)
                        #log_stalk(task_name + "item__attribute_href: " + str(item__attribute_href), enable_log_stalk)


                        log_stalk(task_name + "шаблон: DIV ", enable_log_stalk)
                        links = item.find_elements_by_class_name('serp-url__link')

                        name = task_name + "_" + str(current_page) + " шаблон DIV"
                        #log_stalk(task_name + "name: " + str(name), enable_log_stalk)
                        save_screenshots(SCREENSHOTS_DIR_today, name, " шаблон DIV", driver)
                        log_stalk(task_name + "колво link в links: " + str(len(links)), enable_log_stalk)

                    else:
                        log_stalk(task_name + "шаблон: LI ", enable_log_stalk)
                        links = item.find_elements_by_class_name('link_theme_outer')
                        log_stalk(task_name + "колво link в links: " + str(len(links)), enable_log_stalk)
                except Exception as e:
                    log_stalk(task_name + " не получилось взять  ЛИНКС: " + str(e) + "_", enable_log_stalk)
                    name = task_name + "_" + str(current_page)
                    save_screenshots(SCREENSHOTS_DIR_today, name, " не получилось взять  ЛИНКС", driver)
                    continue
                try:
                    link = links[0]
                    url = link.get_attribute('href')
                except Exception as e:
                    log_stalk(task_name + " не получилось взять  ЛИНКС<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<: " + str(
                        e) + "_", enable_log_stalk)
                    name = task_name + "_" + str(current_page)
                    name = name + "8888888888"
                    save_screenshots(SCREENSHOTS_DIR_today, name, " не получилось взять  ЛИНКС<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", driver)

                    #link = links[0]
                    url = "http://XXXXXXXXXXXXXXX"

                sleep(1)

                if url[:11] == "http://yabs":
                    url = "http://yabs.yandex.ru"
                log_stalk(task_name + "Текущий URL: " + url, enable_log_stalk)
                log_stalk(task_name + "Количество открытых вкладок ITEM begin " + str(len(driver.window_handles)), enable_log_stalk)

                if is_same_site(ttarget_url, url):
                    log_stalk(task_name + "###  ЗАХОДИМ НА ЦЕЛЕВОЙ САЙТ", enable_log_stalk)
                    try:
                        hyperlink.find_element_by_tag_name('a').click()
                    except Exception as e:
                        logging.exception(task_name + "URL can't be visited")

                    log_stalk(task_name + "Количество открытых вкладок AFTER CLICK " + str(len(driver.window_handles)), enable_log_stalk)

                    driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "2_before_wos.png")
                    driver.switch_to.window(driver.window_handles[-1])
                    log_stalk(task_name + "Количество открытых вкладок BEFORE WOS " + str(len(driver.window_handles)), enable_log_stalk)

                    walk_on_site(driver, task_name)
                    driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "3_after_wos.png")

                    log_stalk(task_name + "Количество открытых вкладок " + str(len(driver.window_handles)), enable_log_stalk)
                    if url[:11] == "http://yabs":
                        url = "http://yabs.yandex.ru"
                    log(user=self.task.owner, task=self.task, action='VISIT', extra={'visit_to_TARGET_url': url}, uid=self.uid)
                    #  заходим на целевой сайт
                    for i in range(5):
                        driver.execute_script(f"window.scrollTo(0, {randint(300, 700)});")
                        sleep(randint(12, 24))
                    driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "4_end_wos.png")
                    sleep(randint(10, 6 * 60))

                    not_done_flag = False

                    #driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "5_end_wos.png")
                    exitFlag = True
                    driver.close()
                    driver.quit()
                    #GroupTask.objects.filter(id=self.task.id).update(position=str(current_page) + "." + str(current_position))
                    GroupTask.objects.filter(id=self.task.id).update(position=str(current_page*10 + int(current_position)))
                    #log_stalk(task_name + "Position: " + (str(current_page) + "." + str(current_position)), enable_log_stalk)
                    log_stalk(task_name + "Position: " + (str(current_page*10 + int(current_position))), enable_log_stalk)
                    break

                elif (current_page == 0 and tcompetitor_sites_len == 0) or is_competitor_site(url, tcompetitor_sites):
                    log_stalk(task_name + "###  ЗАХОДИМ на САЙТ КОНКУРЕНТОВ - elif", enable_log_stalk)
                    if ((random.choice([True, False]) == True) and number_competitor_visit >= 1) :
                        log_stalk(task_name + "###  ЗАХОДИМ на САЙТ КОНКУРЕНТОВ", enable_log_stalk)
                        log(user=self.task.owner, task=self.task, action='VISIT', extra={'visit_to_CONCURENT_url': url}, uid=self.uid)
                        link.click()
                        driver.switch_to.window(driver.window_handles[-1])
                        #  заходим к конкурентам
                        for i in range(5):
                            #sleep(randint(3, 5))
                            sleep(randint(4, 6))
                            driver.execute_script(f"window.scrollTo(0, {randint(300, 800)});")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        number_competitor_visit -= 1
                        log_stalk(task_name + "Осталось зайти к конкурентам: " + str(number_competitor_visit), enable_log_stalk)
            if (exitFlag):
                break
            sleep(10)
            msg = "pager - Количество открытых вкладок " + str(len(driver.window_handles))
            log_stalk(task_name + msg, enable_log_stalk)
            driver.save_screenshot(SCREENSHOTS_DIR_today + task_name + "6_pager.png")
            pager = driver.find_element_by_class_name('pager')
            next_page = pager.find_elements_by_tag_name('a')[-1]
            next_page.click()
            sleep(3)
            #current_page_number = driver.find_element_by_class_name('pager__item_current_yes').get_attribute('innerText')
            current_page_number = ""
            log(user=self.task.owner, task=self.task, action='NEXT_PAGE', extra={'current_page': current_page_number}, uid=self.uid)
        if not_done_flag:
            log_stalk(task_name + "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++НА ЦЕЛЕВОЙ САЙТ ЗАХОДА НЕ БЫЛО!!!!!", enable_log_stalk)
            log_stalk(task_name + "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++not_done!!!!! - " + str(self.task.not_done), enable_log_stalk)
            GroupTask.objects.filter(id=self.task.id).update(not_done=F('not_done') + 1)
            not_done_flag = False

    def generate_browser_configuration(self, proxy_list: str, task_name: str, task_id: int) -> Dict[str, str]:
        config = {'user-agent': generate_user_agent(os=('win', 'mac')), 'resolution': get_random_screen_resolution()}
        log_proxy(f"{task_name}КОНФИГУРАЦИЯ БРАУЗЕРА - USER-AGENT: {config}", enable_log_proxy)
        i = 0
        ModelProxy = apps.get_model('walker_panel', 'Proxy' + proxy_list.replace('P', ''))
        while True:
            if not ModelProxy.objects.filter(owner=self.task.owner).count():
                return config
            if i > 0:
                log_proxy( f"{task_name}КОНФИГУРАЦИЯ БРАУЗЕРА - {i} итерация ВЫБРАННЫЙ ПРОКСИ ИСПОЛЬЗУЕТСЯ: {proxy.host}:{proxy.port}", enable_log_proxy)
            proxy = random.choice(ModelProxy.objects.filter(owner=self.task.owner))
            thread_data.proxy = f"{proxy.host}:{proxy.port}"
            log_proxy(f"{task_name}КОНФИГУРАЦИЯ БРАУЗЕРА - {i} итерация ВЫБРАН ПРОКСИ: {thread_data.proxy}", enable_log_proxy)
            i += 1
            if not UsedProxy.objects.filter(address=f"{thread_data.proxy}").exists():
                break
            sleep(30)
        if proxy.username:
            config['proxy'] = f"{proxy.username}:{proxy.password}@{thread_data.proxy}"
        else:
            config['proxy'] = f"{thread_data.proxy}"
        #usedproxy_add_addr(str(task_id), thread_data.proxy)
        return config

    def change_region(self, driver: Chrome, task_name: str, city: str) -> None:
        thread_data.change_region = "-"
        free_captcha(task_name, 'СМЕНА РЕГИОНА: перед GEOLINK click', driver)
        sleep(3)
        self.click(task_name, "СМЕНА РЕГИОНА: ПОСЛЕ НАЖАТИЯ на GEOLINK", "class", "geolink", "Местоположение", driver)
        sleep(7)
        free_captcha(task_name, 'СМЕНА РЕГИОНА: после click geolink', driver)
        save_screenshots(SCREENSHOTS_DIR_today, task_name, "СМЕНА РЕГИОНА: ПОСЛЕ НАЖАТИЯ на GEOLINK", driver)
        log_stalk(f"{task_name}СМЕНА РЕГИОНА: ПОСЛЕ НАЖАТИЯ на GEOLINK {driver.title}", enable_log_stalk)
        i = 0
        sleep(3)
        while "Местоположение" in driver.title:
            log_stalk(f"{task_name}СМЕНА РЕГИОНА: i = {str(i)} - {driver.title}", enable_log_stalk)
            if i > 0:
                driver.refresh()
                log_stalk(f"{task_name}СМЕНА РЕГИОНА: DRIVER REFRESH, i = {str(i)} - {driver.title}", enable_log_stalk)
            if i >= 2:
                send_email(email_dev, "Местоположение залипло", email_titel, f"i > 2")
            sleep(7)
            driver.find_element_by_id('city__front-input').click()
            save_screenshots(SCREENSHOTS_DIR_today, task_name, "СМЕНА РЕГИОНА: ПОСЛЕ CLICK ПО ПОЛЮ city__front-input", driver)
            log_stalk(f"{task_name}СМЕНА РЕГИОНА: ПОСЛЕ CLICK ПО ПОЛЮ city__front-input, Title = {driver.title}", enable_log_stalk)
            try:
                #letter_by_letter(task_name, "id", "city__front-input", city, driver, False)
                letter_by_letter(f"{task_name}СМЕНА РЕГИОНА:", "id", "city__front-input", city, driver, False)
                geo_input = driver.find_element_by_class_name('input__popup_type_geo')
                free_captcha(task_name, 'change region: TRY change region, перед input__popup_type_geo', driver)
                localities = geo_input.find_elements_by_tag_name('li')
                for locality in localities:
                    geo_data = json.loads(locality.get_attribute('data-bem'))
                    item = geo_data['b-autocomplete-item']
                    if item['title'] == city:
                        locality.click()
                        sleep(7)
                        log_stalk(f"{task_name}СМЕНА РЕГИОНА: TRY, Title = {driver.title}", enable_log_stalk)
                        save_screenshots(SCREENSHOTS_DIR_today, task_name, "СМЕНА РЕГИОНА: TRY", driver)
                        thread_data.change_region = "TRY"
                        return
                city_input.send_keys(Keys.ENTER)
                sleep(7)
            except Exception as e:
                letter_by_letter(f"{task_name}СМЕНА РЕГИОНА:", "class", "input__control", city, driver, False)
                driver.find_element_by_class_name('input__control').send_keys(Keys.ENTER)
                sleep(7)
                log_stalk(f"{task_name}СМЕНА РЕГИОНА: EXCEPT, Title = {driver.title}", enable_log_stalk)
                save_screenshots(SCREENSHOTS_DIR_today, task_name, "СМЕНА РЕГИОНА: EXCEPT", driver)
                thread_data.change_region = "EXCEPT"
            i += 1
            sleep(3)

    def click(self, task_name: str, where: str, by_type: str, by_identifier: str, need_title: str, driver: Chrome):
        i = 0
        log_stalk(f"{task_name}{where} текущая страница {i} - {driver.title}", enable_log_stalk)
        while not need_title in driver.title:
            sleep(2)
            save_screenshots(SCREENSHOTS_DIR_today, task_name, "CLICK " + by_identifier, driver)
            log_stalk(f"{task_name}{where} Количество открытых вкладок до клика = {len(driver.window_handles)}", enable_log_stalk)
            sleep(3)
            if by_type == "xpath":
                element = driver.find_element_by_xpath(by_identifier)
            if by_type == "id":
                element = driver.find_element_by_id(by_identifier)
            if by_type == "class":
                element = driver.find_element_by_class_name(by_identifier)
            element.click()
            sleep(10)
            log_stalk(f"{task_name}{where} Количество открытых вкладок после клика = {len(driver.window_handles)}", enable_log_stalk)
            save_screenshots(SCREENSHOTS_DIR_today, task_name, where + " Количество открытых вкладок после клика", driver)
            if need_title in driver.title:
                log_stalk(f"{task_name}{where} RETURN: текущая страница {i} - {driver.title}", enable_log_stalk)
                return
            if len(driver.window_handles) > 1:
                send_email(email_dev, where, email_titel, f" ВКЛАДОК > 1 ")
                for handle in driver.window_handles:
                    driver.switch_to_window(handle)
                    log_stalk(task_name + " - ВКЛАДКА = " + driver.title, enable_log_stalk)
                    #if not "Местоположение" in driver.title:
                    #    send_email(email_dev, where, email_titel, f" window_handles > 1 {driver.title} ")
                    send_email(email_dev, where, email_titel, f" ВКЛАДКА = {driver.title} ")
                    if "Местоположение" in driver.title:
                        log_stalk(task_name + " - RETURN, ВКЛАДКА = " + driver.title, enable_log_stalk)
                        return
            sleep(5)
            """
            try:
                java_script = "document.getElementsByClassName('" + by_identifier + "')[0].click();"
                driver.execute_script(java_script)
                log_stalk(task_name + " - TRY JAVA_SCRIPT click " + by_identifier + " --" + str(i), enable_log_stalk)
                log_stalk(task_name + "Количество открытых вкладок " + str(len(driver.window_handles)), enable_log_stalk)
                save_screenshots(SCREENSHOTS_DIR_today, task_name, "TRY JAVA_SCRIPT CLICK " + str(i), driver)
                if need_title in driver.title:
                    log_stalk(f"{task_name}{where} RETURN JAVA_SCRIPT: текущая страница {i} - {driver.title}", enable_log_stalk)
                    return
            except Exception as detail:
                log_stalk(task_name + " - EXCEPT JAVA_SCRIPT click " + by_identifier + " --" + str(i) + str(detail), enable_log_stalk)
                save_screenshots(SCREENSHOTS_DIR_today, task_name, "EXCEPT JAVA_SCRIPT CLICK " + str(i), driver)
                sleep(10)
            """
            i += 1
            driver.refresh()
            sleep(8)

def get_driver(config: Dict) -> Chrome:
    options = ChromeOptions()
    capabilities = DesiredCapabilities.CHROME
    options.add_argument(f"--window-size={config['resolution']}")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={config['user-agent']}")
    options.add_argument("--headless")
    if config.get('proxy'):
        options.add_argument(f'--proxy-server={config["proxy"]}')
    return Chrome("./webdriver/chromedriver", options=options, desired_capabilities=capabilities)

def convert(l:list):
    s = [str(i) for i in l]
    res = "".join(s)
    return res

def thread_enum(where: str):
    log_run(where + line_short, enable_log_stalk)
    log_run(where + " КОЛИЧЕСТВО ПОТОКОВ: " + str(active_count()), enable_log_run)
    for thread in threading.enumerate():
        log_run(where + " ПОТОК: " + thread.name, enable_log_run)
    log_run(where + line_short, enable_log_stalk)

#def thread_start(task: task, task_id: int, hour: int, minutes: int, run_text: str):
def thread_start(threads: dict, task: GroupTask, task_id: int, hour: int, minutes: int, run_text: str):
    thread_id = f"Task{task_id}.{hour}:{minutes}.{random_string(3)}"
    log_run(run_text + "Задача " + str(task_id) + ": СТАРТ имя потока " + thread_id, enable_log_run)
    threads[thread_id] = TaskRunner(task=task)
    threads[thread_id].name = thread_id
    threads[thread_id].start()

def run():
    timenow = uptime_obj()
    # СБРАСЫВАНИЕ КЭШЕЙ РАБОТЫ БОТА ПОСЛЕ ПЕРЕЗАГРУЗКИ
    if timenow.days == 0 and timenow.hours == 0 and timenow.minutes <= 10:
        log_run("RUN - СБРАСЫВАНИЕ КЭШЕЙ РАБОТЫ БОТА ПОСЛЕ ПЕРЕЗАГРУЗКИ: uptime менее 5 минут", enable_log_run)
        ci = CommonInfo.objects.get(id=1)
        if not ci.reboot_reset:
            log_run("RUN - СБРАСЫВАНИЕ КЭШЕЙ РАБОТЫ БОТА ПОСЛЕ ПЕРЕЗАГРУЗКИ: reboot_reset = False", enable_log_run)
            tasks_reset_reboot()
            ci.reboot_reset = True
            ci.reboot_reset_time = timezone.now()
            ci.save()
    # НОЧНОЕ СБРАСЫВАНИЕ КЭШЕЙ РАБОТЫ БОТА
    if datetime.now().hour == 4:
        ci = CommonInfo.objects.get(id=1)
        if not ci.today_reset:
            log_run("RUN - НОЧНОЕ СБРАСЫВАНИЕ КЭШЕЙ РАБОТЫ БОТА", enable_log_run)
            tasks_reset_night()
            tasks_reset_not_done()
            # удаляем вчерашнее расписание
            scheduler_clear()
            usedproxy_clear()
            cih_save(email_titel)
            ci_reset_status(True)
    if datetime.now().hour == 5:
        create_dir(SCREENSHOTS_DIR_today)
        ci = CommonInfo.objects.get(id=1)
        if ci.today_reset:
            ci_reset_status(False)

    # ГЕНЕРАЦИЯ РАСПИСАНИЯ ДЛЯ ЗАДАЧ БОТА
    if datetime.now().hour == 6:
        log_run("RUN - ГЕНЕРАЦИЯ РАСПИСАНИЯ ДЛЯ ЗАДАЧ БОТА", enable_log_run)
        if Scheduler.objects.all().count() == 0:
            for task in GroupTask.objects.filter(status=True):
                scheduler_generate(task.launches_per_day, task.id, hour_start, hour_end)

    # ЗАПУСК ЗАДАЧ БОТА В ПОТОК
    run_text = "ЗАПУСК ЗАДАЧ В ПОТОК "
    threads = {}
    while hour_start <= datetime.now().hour < hour_end:
        try:
            log_run(run_text + line_double + ">", enable_log_stalk)
            thread_enum(run_text)
            for task in GroupTask.objects.filter(status=True).order_by('id'):
                if task.launches_per_day > task.running_today:
                    shed = Scheduler.objects.get(task_id=task.id)
                    shed = shed.get_schedule()
                    shed_len = len(shed)
                    element = shed[task.running_today]
                    log_run(run_text + "Задача " + str(task.id) + ": следующий запуск задачи в " + str(element) + " (element = " + str(task.running_today) + ")", enable_log_run)
                    hour = element[0]
                    minutes = element[1]
                    if datetime.now().hour == hour:
                        log_run(run_text + "Задача " + str(task.id) + ": час = " + str(hour), enable_log_run)
                        if datetime.now().minute == minutes:
                            ##log_run(run_text + "Задача " + str(task.id) + ": минуты = " + str(minutes), enable_log_run)
                            #thread_id = f"Task{task.id}.{hour}:{minutes}.{random_string(3)}"
                            #log_run(run_text + "Задача " + str(task.id) + ": СТАРТ имя потока " + thread_id, enable_log_run)
                            #threads[thread_id] = TaskRunner(task=task)
                            #threads[thread_id].name = thread_id
                            #threads[thread_id].start()
                            thread_start(threads, task, task.id, hour, minutes, run_text)
                            if task.launches_per_day > (task.running_today + 1) and shed_len != 1:
                                element_next = shed[task.running_today + 1]
                                hour_next = element_next[0]
                                minutes_next = element_next[1]
                                log_run(run_text + "Задача " + str(task.id) + ": NEXT = " + str(hour_next) + ":" + str(minutes_next), enable_log_run)
                                if element[0] == element_next[0] and element[1] == element_next[1]:
                                    thread_start(threads, task, task.id, hour, minutes, run_text)
                                    #thread_id = f"Task{task.id}.{hour}:{minutes}.{random_string(3)}"
                                    #log_run(run_text + "Задача " + str(task.id) + ": СТАРТ имя потока " + thread_id, enable_log_run)
                                    #threads[thread_id] = TaskRunner(task=task)
                                    #threads[thread_id].name = thread_id
                                    #threads[thread_id].start()
                else:
                    log_run(run_text + "Задача " + str(task.id) + ": ВСЕ ЗАПЛАНИРОВАННЫЕ НА ДЕНЬ ЗАПУСКИ ЗАДАЧИ ВЫПОЛНЕНЫ", enable_log_run)
            log_run(run_text + "<" + line_double, enable_log_stalk)
            sleep(60)
        except KeyboardInterrupt:
            for task_id, task_runner in threads.items():
                task = GroupTask.objects.get(pk=task_id)
                log_run("task.running_today( KeyboardInterrupt) = " + str(task.running_today), enable_log_run)
                task.running_today += 1
                task.save()
    sleep(60)
