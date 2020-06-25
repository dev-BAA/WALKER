import os, platform
import logging
import imghdr
import urllib

from typing import Dict
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities

from walker_panel.models import *
from scripts.common_functions import *

base_url = 'http://rucaptcha.com'
req_url = base_url + '/in.php'
res_url = base_url + '/res.php'
load_url = base_url + '/load.php'

stngs = Setting.objects.get(id=2)
enable_log_run = stngs.enable_log_run
enable_log_stalk = stngs.enable_log_stalk
enable_log_proxy = stngs.enable_log_proxy

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
                    log_stalk(task_name + " GET КАПЧА src 1", enable_log_stalk)
                    #captcha_src = driver.find_elements_by_class_name('form__captcha')[0].get_attribute('src')
                    #captcha_src = driver.find_elements_by_class_name('captcha_image')[0].get_attribute('src')
                    #captcha_src = driver.find_elements_by_class_name('captcha__image')[0].get_attribute('src')
                    captcha_src = driver.find_elements_by_class_name('captcha__image')[0].get_attribute('src')
                    captcha_src2 = driver.find_elements_by_class_name('captcha__image').get_attribute('src')
                    captcha_src3 = driver.find_elements_by_class_name('captcha__image')
                    captcha_src4 = driver.find_element_by_xpath("//div[@class='captcha__image']/img").get_attribute("src")
                    log_stalk(task_name + " GET КАПЧА src 2 - " + str(captcha_src), enable_log_stalk)
                    log_stalk(task_name + " GET КАПЧА src 22 - " + str(captcha_src2), enable_log_stalk)
                    log_stalk(task_name + " GET КАПЧА src 23 - " + str(captcha_src3), enable_log_stalk)
                    log_stalk(task_name + " GET КАПЧА src 24 - " + str(captcha_src4), enable_log_stalk)
                    save_png(CAPTCHAS_DIR, taskname, str(captcha_src))
                except Exception as e:
                    print(e)
                    log_stalk(task_name + " GET КАПЧА src " + str(e), enable_log_stalk)
                #save_png(CAPTCHAS_DIR, taskname, captcha_src)


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

