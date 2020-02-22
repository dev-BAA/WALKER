import logging
import os, platform
import subprocess
import asyncio
import string, random

import psutil
import smtplib

from time import sleep
from datetime import datetime, timedelta
from user_agent import generate_user_agent

from email.mime.text import MIMEText
#from email.MIME.Text import MIMEText
#from email.MIME.Multipart import MIMEMultipart
#from email.header    import Header

from selenium.webdriver import Chrome
from typing import List, Union, Dict, Tuple, Optional as Opt

from aiohttp import ClientSession, BasicAuth
from django.db import IntegrityError

#from walker_panel.models import Proxy, Proxy1
from walker_panel.models import *
#from sql_querys import usedproxy_add_addr

logger = logging.getLogger('bot')

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
line = "--------------------------------------------------"
line_short = "-------------------------"
line_double = "===================================================="
line_double_short = "=========================="
enable_log = True

def log_run(string: str, enable: bool):
    if enable:
        logger.info(string)

def log_user(string: str, enable: bool):
    if enable:
        logger.info(string)

def log_stalk(string: str, enable: bool):
    if enable:
        logger.info(string)

def log_proxy(string: str, enable: bool):
    if enable:
        logger.info(string)

def check_dev():
    if str(platform.node()) == "DEVWALK":
        return True
    return False

def save_html(path: str, name: str, driver: Chrome):
    with open(path + name + ".html", 'w') as f:
        f.write(driver.page_source)

def save_png(path: str, name: str, url: str):
    file = path + name + ".png"
    urllib.request.urlretrieve(url, file)

def save_screenshots(path: str, name: str, where: str, driver: Chrome):
    with open(path + name + where + ".html", 'w') as f:
        f.write(driver.page_source)
    driver.save_screenshot(path + name + where + ".png")

def save_screenlog(driver: Chrome, path: str, name: str, where: str):
    _string = name + where
    with open(path + _string + ".html", 'w') as f:
        f.write(driver.page_source)
    driver.save_screenshot(path + _string + ".png")
    log_stalk(_string + " (png, html)", enable_log)

def create_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def random_string(stringLength: int):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def string_to_decimal(string: str):
    lenth = len(string)
    string_decimal = ""
    for number in range(lenth):
        if string[number].isdecimal():
            string_decimal = string_decimal + string[number]
    return string_decimal

def get_prestart_delay() -> int:
    if check_dev():
        return 0
    else:
        return randint(10*60, 35*60)

def send_email(email_to, sbjct: str, frm: str, mesage: str):
    sender = 'site.walker@yandex.ru'
    sender_password = '(OL>.lo9'
    mail_lib = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    mail_lib.login(sender, sender_password)
    msg = MIMEText(mesage.encode('utf-8'), _charset='utf-8')
    msg['Subject'] = sbjct
    msg['From'] = frm
    msg['To'] = email_to
    mail_lib.sendmail(sender, email_to, msg.as_string())

def get_perf(task: str, info: str, ram_low: int, enable: bool):
    log_run(task + " " + info + " - CPU - " + str(psutil.cpu_percent()), enable)
    log_run(task + " " + info + " - RAM common - " + str(psutil.virtual_memory()), enable)

    ram_0 = psutil.virtual_memory()[0] // 1048576
    ram_0_wd = psutil.virtual_memory()[0]

    ram_1 = psutil.virtual_memory()[1] // 1048576
    ram_1_wd = psutil.virtual_memory()[1]

    ram_2 = psutil.virtual_memory()[2] // 1048576
    ram_2_wd = psutil.virtual_memory()[2]

    ram_3 = psutil.virtual_memory()[3] // 1048576
    ram_3_wd = psutil.virtual_memory()[3]

    ram_4 = psutil.virtual_memory()[4] // 1048576
    ram_4_wd = psutil.virtual_memory()[4]

    ram_5 = psutil.virtual_memory()[5] // 1048576
    ram_5_wd = psutil.virtual_memory()[5]

    ram_6 = psutil.virtual_memory()[6] // 1048576
    ram_6_wd = psutil.virtual_memory()[6]

    log_run(task + " " + info + " - RAM [0] total - " + str(ram_0) + " Мб", enable)
    log_run(task + " " + info + " - RAM [0] total - " + str(ram_0_wd), enable)
    log_run(task + " " + info + " - RAM [1] available - " + str(ram_1) + " Мб", enable)
    log_run(task + " " + info + " - RAM [1] available - " + str(ram_1_wd), enable)
    log_run(task + " " + info + " - RAM [2] percent - " + str(ram_2) + " Мб", enable)
    log_run(task + " " + info + " - RAM [2] percent - " + str(ram_2_wd), enable)
    log_run(task + " " + info + " - RAM [3] used - " + str(ram_3) + " Мб", enable)
    log_run(task + " " + info + " - RAM [3] used - " + str(ram_3_wd), enable)
    log_run(task + " " + info + " - RAM [4] free - " + str(ram_4) + " Мб", enable)
    log_run(task + " " + info + " - RAM [4] free - " + str(ram_4_wd), enable)
    log_run(task + " " + info + " - RAM [5] active - " + str(ram_5) + " Мб", enable)
    log_run(task + " " + info + " - RAM [5] active - " + str(ram_5_wd), enable)
    log_run(task + " " + info + " - RAM [6] inactive - " + str(ram_6) + " Мб", enable)
    log_run(task + " " + info + " - RAM [6] inactive - " + str(ram_6_wd), enable)

    if ram_1 < ram_low:
        send_email("butalov.a@ya.ru", "RAM доступно меньше " + str(ram_low), 'Site Walker HOME', f"{task} \n ГДЕ: {info} \n RAM ВСЕГО: {ram_0} Мб \n RAM доступно для процессов: {ram_1} \n RAM используется в процентах: {ram_2_wd} \n RAM используется: {ram_3} Мб \n RAM free: {ram_4} Мб")

def check_free_ram(task: str, ram_low: int, where: str, enable: bool):
    while True:
        free_ram = psutil.virtual_memory()[1] // 1048576
        if free_ram < ram_low:
            log_run(task + "ПРОВЕРКА СВОБОДНОЙ RAM (" + where + "), МАЛО: " + str(free_ram) + " Мб", enable)
            #send_email("butalov.a@ya.ru", "RAM меньше 400", 'Site Walker HOME', f"{task} \n ГДЕ: FREE RAM CHECK - FAIL - {str(free_ram)}")
            sleep(5*60)
        else:
            log_run(task + "ПРОВЕРКА СВОБОДНОЙ RAM (" + where + "), ДОСТАТОЧНО: " + str(free_ram) + " Мб", enable)
            break

"""
def check_proxy(proxyip: str) -> bool:
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxyip})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req=urllib.request.Request('http://www.yandex.ru')
        sock=urllib.request.urlopen(req)
        '''
        ## webpage = urllib.request.urlopen(req).read()
        #webpage.encoding = 'utf-8'
        #title = str(webpage).split('<title>')[1].split('</title>')[0]
        ## soup = BeautifulSoup(webpage, 'html.parser')
        ## log_proxy(f"{task_name} check proxy2", enable_log_proxy)
        #log_proxy(f"{task_name} urllib page Title: " + str(title), enable_log_proxy)
        ## ttl = str(soup.title)
        #log_proxy(f"{task_name} urllib page Title: " + str(ttl.decode('utf-8')), enable_log_proxy)
        ## log_proxy(f"{task_name} urllib page Title: " + ttl, enable_log_proxy)
        ## if ttl.find("Яндекс") != -1:
        ##     log_proxy(f"{task_name} Яндекс есть, прокси норм!", enable_log_proxy)
        ## else:
        ##     log_proxy(f"{task_name} нет Яндекса!", enable_log_proxy)
        '''
    except urllib.error.HTTPError as e:
        #log_proxy(f"{task_name} check proxy Error1: " + e.code, enable_log_proxy)
        print('Error code: ', e.code)
        return e.code
    except Exception as detail:
        print("ERROR:", detail)
        #log_proxy(f"{task_name} check proxy Error2: " + detail, enable_log_proxy)
        return True
    return False
"""

def get_current_time(task_name):
    logger.info(task_name + " Текущее время " + str(datetime.now().hour) + ":" + str(datetime.now().minute) + ":" + str(datetime.now().second) + ":" + str(datetime.now().microsecond))

def extract_proxy(line: str) -> Tuple[str, str, Opt[str], Opt[str]]:
    try:
        if len(line.split(':')) == 2:
            host, port = line.split(':')
            username = password = None
        elif len(line.split(':')) == 4:
            host, port, username, password = line.split(':')
        else:
            logger.error(f'Proxy line parsing failed: {line}')
            return

        return host, port, username, password
    except ValueError as e:
        logger.error(f'Proxy line parsing failed: {line}. Exception message: {e}')


async def check_proxy_enable(host: str, port:str, username: str, password: str) -> Dict[str, Union[str, bool]]:
    async with ClientSession() as session:
        if username is None:
            proxy_auth = None
        else:
            proxy_auth = BasicAuth(username, password)
        async with session.get("http://python.org",
                               proxy=f"http://{host}:{port}",
                               proxy_auth=proxy_auth) as resp:
            return {'host': host,
                    'port': port,
                    'username': username,
                    'password': password,
                    'enabled': resp.status == 200}


async def save_proxies(user, text_data) -> List[Proxy]:
    lines = text_data.split('\n')
    proxies = []
    coroutines = []

    for line in lines:
        try:
            host, port, username, password = extract_proxy(line.strip(' \n\r'))
            coroutines.append(check_proxy_enable(host, port, username, password))
        except ValueError as e:
            print(e)

    raw_proxies = await asyncio.gather(*coroutines)
    for item in raw_proxies:
        try:
            proxy, was_created = Proxy.objects.get_or_create(owner=user,
                                                             host=item['host'],
                                                             port=item['port'],
                                                             username=item['username'],
                                                             password=item['password'],
                                                             enabled=item['enabled'])
        except IntegrityError as e:
            print(e)
        # proxies.append(proxy)
    #
    # return proxies

async def save_proxies1(user, text_data) -> List[Proxy]:
    lines = text_data.split('\n')
    proxies = []
    coroutines = []

    for line in lines:
        try:
            host, port, username, password = extract_proxy(line.strip(' \n\r'))
            coroutines.append(check_proxy_enable(host, port, username, password))
        except ValueError as e:
            print(e)

    raw_proxies = await asyncio.gather(*coroutines)
    for item in raw_proxies:
        try:
            proxy, was_created = Proxy1.objects.get_or_create(owner=user,
                                                             host=item['host'],
                                                             port=item['port'],
                                                             username=item['username'],
                                                             password=item['password'],
                                                             enabled=item['enabled'])
        except IntegrityError as e:
            print(e)
        # proxies.append(proxy)
    #
    # return proxies

def is_service_running(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'status'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0
