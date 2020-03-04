import os, platform
import logging
import random
import operator
import datetime

from time import sleep
from datetime import datetime, timedelta
from random import randint, choice
from uuid import uuid4, UUID

from django.utils import timezone
from walker_panel.models import *
from scripts.common_functions import check_dev, send_email

common_info_table_id = 1
logger = logging.getLogger('sql_querys')

def log(user: User, task: GroupTask, action: str, level: str = 'info', extra: dict = None, uid: UUID = None, pid: str = None):
    log_entry = GroupLog(owner=user, task=task, action=action, extra=json.dumps(extra), level=level, uid=uid, pid=pid)
    log_entry.save()
    logger.info("Task " + str(task.id) + ": " + action)

# Сбрасываем параметры всех задач после внезапной перезагрузки
def tasks_reset_reboot():
    for task in GroupTask.objects.all():
        task.template_div = False
        task.save()

# Сбрасываем параметры всех задач во время ночьного обслуживания
def tasks_reset_night():
    for task in GroupTask.objects.all():
        task.template_div = False
        task.not_done = 0
        task.running_today = 0
        task.position_yesterday = task.position
        task.save()

# Сбрасываем счетчик не выполненных (из за глубины поиска) задач
def tasks_reset_not_done():
    for task in GroupTask.objects.all():
        task.not_done = 0
        task.save()

def scheduler_generate(launches_per_day: int, task_id: int, hour_start: int, hour_end: int):
    aa = []
    i = launches_per_day
    while i > 0:
        a = []
        hour = randint(hour_start, hour_end - 1)
        a.append(hour)
        minute = randint(0, 59)
        a.append(minute)
        aa.append(a)
        i -= 1
    aa = sorted(aa, key=operator.itemgetter(0, 1))
    she = Scheduler(task_id=task_id, schedule="")
    she.set_schedule(aa)
    she.save()

def scheduler_clear():
    Scheduler.objects.all().delete()

def usedproxy_add_addr(task: str, address: str, pid: str, thread: str):
    up = UsedProxy(task=task, address=address, pid=pid, template_div=False, thread=thread)
    up.save()

def usedproxy_updt_div(addr: str, template_div: bool):
    up = UsedProxy.objects.get(address=addr)
    up.template_div = template_div
    up.save()

def usedproxy_remove_addr(addr: str):
    UsedProxy.objects.filter(address=addr).delete()

def usedproxy_clear():
    UsedProxy.objects.all().delete()

def ci_task_finished():
    ci = CommonInfo.objects.get(id=common_info_table_id)
    ci.task_finished = ci.task_finished + 1
    ci.save()

def ci_task_crashed():
    ci = CommonInfo.objects.get(id=common_info_table_id)
    ci.task_crashed = ci.task_crashed + 1
    ci.save()

def ci_task_capched():
    ci = CommonInfo.objects.get(id=common_info_table_id)
    ci.task_capched = ci.task_capched + 1
    ci.save()

def ci_reset_status(flag: bool):
    if flag:
        ci = CommonInfo.objects.get(id=common_info_table_id)
        ci.task_finished = 0
        ci.task_crashed = 0
        ci.task_capched = 0
        ci.today_reset = True
        ci.save()
    if not flag:
        #ci = CommonInfo.objects.all()[0]
        ci = CommonInfo.objects.get(id=common_info_table_id)
        ci.today_reset = False
        ci.save()

def ci_zero_balance(set_parametr: bool):
    if set_parametr:
        ci = CommonInfo.objects.get(id=common_info_table_id)
        ci.zero_balance = True
        ci.save()
    else:
        ci = CommonInfo.objects.get(id=common_info_table_id)
        ci.zero_balance = False
        ci.save()

def cih_save(email_titel: str):
    ci = CommonInfo.objects.get(id=common_info_table_id)
    date = timezone.now() - timezone.timedelta(days=1)
    cih = CommonInfoHistory(create_time=date.date(), task_finished=ci.task_finished, task_crashed=ci.task_crashed, task_capched=ci.task_capched)
    cih.save()
    if ci.task_crashed >= 4:
        send_email("butalov.a@ya.ru", "crashed", email_titel, " ci.task_crashed = " + str(ci.task_crashed))

def ci_reboot_reset():
    ci = CommonInfo.objects.get(id=common_info_table_id)
    #date = timezone.now() - timezone.timedelta(days=1)
    if ci.reboot_reset:
        ci.reboot_reset = False
        ci.reboot_reset_time = timezone.now()
        ci.last_task_ended = timezone.now()
        ci.save()

def ci_task_finish():
    ci = CommonInfo.objects.get(id=common_info_table_id)
    ci.last_task_ended = timezone.now()
    ci.save()

def error_save(task_name: str, proxy: str, city: str, template_div: bool, error_user_agent: str, error_flag: str, error_text: str):
    err = Errors(error_task_name=task_name, error_proxy=proxy, error_city=city, template_div=template_div, error_user_agent=error_user_agent, error_flag=error_flag ,error_text=error_text)
    err.save()
