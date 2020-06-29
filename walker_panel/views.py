import asyncio
import datetime
import psutil
import logging
from typing import Optional
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone

import urllib, base64, io
import numpy as np
import matplotlib.pyplot as plt

from walker_panel.forms import *
from walker_panel.models import *
from scripts.sql_querys import *
from scripts.common_functions import *
from scripts.bot_getpage import *

last_month = datetime.today() - timedelta(days=30)

@login_required(login_url='/sign-in/')
def groups(request: WSGIRequest):
    groups = Group.objects.filter(owner=request.user.id)
    commoninfo = CommonInfo.objects.get(pk=1)
    gtasks = GroupTask.objects.all().count()
    return render(request, 'walker_panel/groups.html',
                  {'groups': groups, 'gtasks': gtasks, 'commoninfo': commoninfo, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def group_page(request: WSGIRequest, group_id: Optional[int] = None):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data.get('id'):
                group = form.save(commit=False)
                group.owner = request.user
                group.save()
            else:
                instance = get_object_or_404(Group, id=form.cleaned_data.get('id'))
                form = GroupForm(request.POST or None, instance=instance)
                form.save()
                group_tasks = GroupTask.objects.filter(target_group_id=group_id)
                for task in group_tasks:
                    task.weekend = instance.weekend
                    task.save()
            return redirect('/groups/')
        return render(request, 'walker_panel/group.html',
                      {'form': form, 'is_walker_enable': is_service_running('walker')})
    else:
        if group_id:
            group = Group.objects.get(id=group_id)
            group_tasks = GroupTask.objects.filter(target_group_id=group_id).order_by('id')
            return render(request, 'walker_panel/group.html',
                          {'form': GroupForm(instance=group), 'is_walker_enable': is_service_running('walker'), 'group_tasks': group_tasks, 'group': group})
        return render(request, 'walker_panel/group.html',
                      {'form': GroupForm(), 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def gtask_page(request: WSGIRequest, group_id: Optional[int] = None, gtask_id: Optional[int] = None):
    stngs = Setting.objects.get(id=2)
    hour_start = datetime.now().hour + 1
    hour_end = stngs.workers_time_end
    if request.method == 'POST':
        form = GTaskForm(request.POST)
        lpd = int(request.POST['launches_per_day'])
        if form.is_valid():
            if Scheduler.objects.filter(task_id=gtask_id).count() != 0:
                Scheduler.objects.get(task_id=gtask_id).delete()
                scheduler_generate(lpd, gtask_id, hour_start, hour_end)
                task = GroupTask.objects.get(id=gtask_id)
                task.running_today = 0
                task.save()
            if not form.cleaned_data.get('id'):
                gtask = form.save(commit=False)
                gtask.owner = request.user
                gtask.save()
                #gtask.name = f"Задача {gtask.id}"
                #gtask.save()
                scheduler_generate(gtask.launches_per_day, gtask.id, hour_start, hour_end)
            else:
                instance = get_object_or_404(GroupTask, id=form.cleaned_data.get('id'))
                form = GTaskForm(request.POST or None, instance=instance)
                form.save()
            return redirect('/group/' + group_id)
        return render(request, 'walker_panel/gtask.html',
                      {'form': form, 'is_walker_enable': is_service_running('walker')})
    else:
        if gtask_id:
            gtask = GroupTask.objects.get(pk=gtask_id)
            return render(request, 'walker_panel/gtask.html',
                          {'form': GTaskForm(instance=gtask), 'is_walker_enable': is_service_running('walker')})
        tg = Group.objects.get(id=group_id)
        return render(request, 'walker_panel/gtask.html',
                      {'form': GTaskForm(initial={'target_group': tg, 'owner': request.user}), 'groupid': group_id, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def remove_gtask(request: WSGIRequest, group_id: int, gtask_id: int):
    ups = UsedProxy.objects.filter(task=gtask_id)
    for up in ups:
        p = psutil.Process(int(up.pid))
        p.kill()
    UsedProxy.objects.filter(task=gtask_id).delete()
    GroupTask.objects.get(pk=gtask_id).delete()
    return redirect('/group/' + group_id)

@login_required(login_url='/sign-in/')
def remove_group(request: WSGIRequest, group_id: int):
    Group.objects.get(pk=group_id).delete()
    return redirect('/groups/')

@login_required(login_url='/sign-in/')
def remove_proxy(request: WSGIRequest, proxy_id: int):
    Proxy.objects.get(pk=proxy_id).delete()
    return redirect('/proxy/')

@login_required(login_url='/sign-in/')
def remove_proxy1(request: WSGIRequest, proxy_id: int):
    Proxy1.objects.get(pk=proxy_id).delete()
    return redirect('/proxy1/')

@login_required(login_url='/sign-in/')
def change_proxy_status(request: WSGIRequest, proxy_id: int):
    proxy = Proxy.objects.get(pk=proxy_id)
    if proxy.status:
        proxy.status = False
    else:
        proxy.status = True
    proxy.save()
    return redirect('/proxy/')

@login_required(login_url='/sign-in/')
def change_proxy_status1(request: WSGIRequest, proxy_id: int):
    proxy = Proxy1.objects.get(pk=proxy_id)
    if proxy.status:
        proxy.status = False
    else:
        proxy.status = True
    proxy.save()
    return redirect('/proxy1/')

@login_required(login_url='/sign-in/')
def change_gtask_status(request: WSGIRequest, group_id: int, gtask_id: int):
    gtask = GroupTask.objects.get(pk=gtask_id)
    if gtask.status:
        gtask.status = False
    else:
        gtask.status = True
    gtask.save()
    return redirect('/group/' + group_id)

@login_required(login_url='/sign-in/')
def logs(request: WSGIRequest):
    logs = GroupLog.objects.filter(owner=request.user).order_by('-create_time')[:1000]
    return render(request, 'walker_panel/logs.html', {'logs': logs, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def historys(request: WSGIRequest):
    historys = CommonInfoHistory.objects.all()
    return render(request, 'walker_panel/historys.html', {'historys': historys, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def errors(request: WSGIRequest):
    errors = Errors.objects.all()
    return render(request, 'walker_panel/errors.html', {'errors': errors, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def results(request: WSGIRequest):
    results = GroupTask.objects.all().order_by('target_group')
    stngs = Setting.objects.get(id=2)
    return render(request, 'walker_panel/results.html', {'results': results, 'stngs': stngs, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def ap(request: WSGIRequest):
    datatograph = CountActiveProxy.objects.filter(create_time__gte=last_month)
    aplist = []
    dates = []
    for a in datatograph:
        aplist = aplist + [a.active_proxy]
        dates = dates + [a.create_time]
    plt.plot(dates, aplist)
    #plt.show()
    plt.savefig('./screenshots/graph.png')
    plt.close()

    #imgdata = StringIO()
    #fig.savefig(imgdata, format='svg')
    #imgdata.seek(0)

    #data = imgdata.getvalue()
    #return data
    return render(request, 'walker_panel/active_proxy.html', {'datatograph': datatograph, 'is_walker_enable': is_service_running('walker')})

@login_required(login_url='/sign-in/')
def settings(request: WSGIRequest):
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            form_sttngs = Setting.objects.get(id=2)
            form = SettingForm(request.POST, instance = form_sttngs)
            form.save()
        return redirect('/settings/')
    else:
        sttngs = Setting.objects.get(id=2)
        return render(request, 'walker_panel/settings.html',
                      {'form': SettingForm(instance=sttngs), 'is_walker_enable': is_service_running('walker')})

#@login_required(login_url='/sign-in/')
#def getpage(request: WSGIRequest, url: Optional[str] = None):
def getpage(request: WSGIRequest):
    logger = logging.getLogger('bot-getpage')
    if request.method == 'GET':
        url = request.GET['url']
        logger.info(line)
        request_id = random_string(5)
        logger.info("request_id: " + request_id)
        logger.info("URL: " + url)
        conf = generate_browser_configuration('bot-getpage', "P", request_id)
        usedproxy_add_addr("getpage_" + request_id, str(conf['proxy']))
        logger.info("proxy: " + str(conf['proxy']))
        try:
            avi = Avito(url, conf, request_id)
            driver = avi.get_driver(conf)
            logger.info("get driver ")
            html = avi.get_page(driver)
            html1 = avi.get_ip(driver)
        except Exception as e:
            logger.exception('Parsing did catch exception')
        finally:
            driver.quit()
            logger.info("driver quit")
        logger.info("end try")
        usedproxy_remove_addr(str(conf['proxy']))
        logger.info("proxy remove")
    return render(request, 'walker_panel/getpage.html', {'html': html})

def getgglposition(request: WSGIRequest):
    logger = logging.getLogger('bot-ggl')
    if request.method == 'GET':
        url = request.GET['url']
        logger.info(line)
        request_id = random_string(5)
        logger.info("request_id: " + request_id)
        logger.info("URL: " + url)
        conf = generate_browser_configuration('bot-avito', "P", request_id)
        usedproxy_add_addr("getpage_" + request_id, str(conf['proxy']))
        logger.info("proxy: " + str(conf['proxy']))
        try:
            avi = Avito(url, conf, request_id)
            driver = avi.get_driver(conf)
            logger.info("get driver ")
            html = avi.get_page(driver)
        except Exception as e:
            logger.exception('Parsing did catch exception')
        finally:
            driver.quit()
            logger.info("driver quit")
        logger.info("end try")
        usedproxy_remove_addr(str(conf['proxy']))
        logger.info("proxy remove")
    return render(request, 'walker_panel/getpage.html', {'html': html})

@login_required(login_url='/sign-in/')
def proxy(request: WSGIRequest):
    if request.method == 'POST':
        proxy_field_text = request.POST['proxies']
        asyncio.run(save_proxies(user=request.user, text_data=proxy_field_text))

    proxies = Proxy.objects.filter(owner=request.user)
    return render(request, 'walker_panel/proxys.html',
                  {'proxy_form': ProxyForm(),
                   'is_walker_enable': is_service_running('walker'),
                   'proxies': proxies})

@login_required(login_url='/sign-in/')
def proxy1(request: WSGIRequest):
    if request.method == 'POST':
        proxy_field_text = request.POST['proxies']
        asyncio.run(save_proxies1(user=request.user, text_data=proxy_field_text))

    proxies = Proxy1.objects.filter(owner=request.user)

    return render(request, 'walker_panel/proxys1.html',
                  {'proxy_form': ProxyForm(),
                   'is_walker_enable': is_service_running('walker'),
                   'proxies': proxies})

def sign_up(request: WSGIRequest):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            # send_email(email, username, raw_password)
            return redirect('/')
        else:
            return render(request, 'walker_panel/sign-up.html', {'form': form})
    else:
        form = SignUpForm()
    return render(request, 'walker_panel/sign-up.html', {'form': form})

def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not request.user.is_authenticated:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            else:
                #return redirect('/sign-up/')
                text = 'Логин или пароль указан неверно'
                #return redirect('/sign-in/')
                return render(request, 'walker_panel/sign-in.html', {'form': AuthenticationForm(), 'text': text})
        return redirect('/')
    return render(request, 'walker_panel/sign-in.html', {'form': AuthenticationForm()})

def sign_out(request):
    logout(request)
    return redirect('/')
