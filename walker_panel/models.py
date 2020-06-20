import json
from django.db import models
from django.contrib.auth.models import User
from django.db.models import CASCADE
#from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils import timezone
from datetime import datetime, timedelta

class Proxy(models.Model):
    owner = models.ForeignKey(User, on_delete=CASCADE)
    host = models.TextField()
    port = models.IntegerField()
    username = models.TextField(null=True)
    password = models.TextField(null=True)
    enabled = models.BooleanField()
    status = models.BooleanField(default=True)

    class Meta:
        unique_together = ('owner', 'host', 'port')

class Proxy1(models.Model):
    owner = models.ForeignKey(User, on_delete=CASCADE)
    host = models.TextField()
    port = models.IntegerField()
    username = models.TextField(null=True)
    password = models.TextField(null=True)
    enabled = models.BooleanField()
    status = models.BooleanField(default=True)

    class Meta:
        unique_together = ('owner', 'host', 'port')

class UsedProxy(models.Model):
    create_time = models.DateTimeField(default=timezone.now, null=True)
    task = models.TextField(null=True)
    address = models.TextField(null=True)
    pid = models.TextField(null=True)
    template_div = models.BooleanField(null=True)
    thread = models.TextField(null=True)

class Setting(models.Model):
    stalker_page_range = models.IntegerField(default=10)
    workers_time_start = models.IntegerField(default=0)
    workers_time_end = models.IntegerField(default=0)
    rucaptcha_key = models.TextField(null=True)
    email_admin = models.TextField(null=True)
    email_dev = models.TextField(null=True)
    enable_log_run = models.BooleanField(default=False)
    enable_log_stalk = models.BooleanField(default=False)
    enable_log_proxy = models.BooleanField(default=False)

class Scheduler(models.Model):
    task_id = models.IntegerField(default=0)
    schedule = models.CharField(max_length=300)

    def set_schedule(self, x):
        self.schedule = json.dumps(x)
        
    def get_schedule(self):
        return json.loads(self.schedule)

class CommonInfo(models.Model):
    task_finished = models.IntegerField()
    task_crashed = models.IntegerField()
    task_capched = models.IntegerField()
    last_task_ended = models.DateTimeField(null=True)
    zero_balance = models.BooleanField(default=False)
    today_reset = models.BooleanField(default=False)
    reboot_reset = models.BooleanField(default=False)
    reboot_reset_time = models.DateTimeField(default=timezone.now, null=True)

class CommonInfoHistory(models.Model):
    create_time = models.DateTimeField()
    task_finished = models.IntegerField()
    task_crashed = models.IntegerField()
    task_capched = models.IntegerField()

class City(models.Model):
    name = models.CharField(max_length=30, unique=True, default='')

    def __str__(self):
        return self.name

class Group(models.Model):
    PROXY_CHOICES = (
        ("P", 'ПРОКСИ'),
        ("P1", 'ПРОКСИ АКТИВНЫЕ'),
    )
    owner = models.ForeignKey(User, on_delete=CASCADE)
    group_name = models.TextField(default='')
    target_url = models.TextField(null=True)
    competitor_sites = models.TextField(null=True, blank=True)
    city = models.TextField(default=None, null=True)
    proxy_list = models.CharField(default='1', max_length=3, choices=PROXY_CHOICES, help_text="*выберите список прокси адресов для этой группы")
    weekend = models.BooleanField(default=True)

    def __str__(self):
        if self.group_name == None:
            return "ERROR-group NAME IS NULL"
        return str(self.group_name)

    @property
    def count_tasks(self):
        tg = Group.objects.get(group_name=self)
        return GroupTask.objects \
            .filter(target_group=tg).count()

class GroupTask(models.Model):
    owner = models.ForeignKey(User, on_delete=CASCADE)
    target_group = models.ForeignKey(Group, on_delete=CASCADE)
    search_query = models.TextField(null=True)
    launches_per_day = models.IntegerField(default=0)
    running_today = models.IntegerField(default=0)
    not_done = models.IntegerField(default=0)
    #position = models.IntegerField(default=0)
    position = models.TextField(null=True)
    #position_yesterday = models.IntegerField(default=0)
    position_yesterday = models.TextField(null=True)
    status = models.BooleanField(default=True)
    weekend = models.BooleanField(default=True)
    last_start = models.DateTimeField(default=timezone.now, null=True)

    def __str__(self):
        return self.target_group.group_name

class GroupLog(models.Model):
    owner = models.ForeignKey(User, on_delete=CASCADE)
    action = models.TextField(null=True)
    task = models.ForeignKey(GroupTask, on_delete=CASCADE, null=True)
    create_time = models.DateTimeField(default=timezone.now)
    level = models.TextField(default='INFO')
    extra = models.TextField(null=True, default='')
    uid = models.TextField()
    pid = models.TextField(null=True)

class Errors(models.Model):
    error_create_time = models.DateTimeField(default=timezone.now)
    error_task_name = models.TextField(null=True)
    error_proxy = models.TextField(null=True)
    error_city = models.TextField(null=True)
    template_div = models.BooleanField(null=True)
    error_user_agent = models.TextField(null=True)
    error_flag = models.TextField(null=True)
    error_text = models.TextField(null=True)