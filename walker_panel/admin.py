from django.contrib import admin
from . import models

class ProxyAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.Proxy._meta.fields]
  class Meta:
    model = models.Proxy

class Proxy1Admin(admin.ModelAdmin):
  list_display = [field.name for field in models.Proxy1._meta.fields]
  class Meta:
    model = models.Proxy1

class UsedProxyAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.UsedProxy._meta.fields]
  class Meta:
    model = models.UsedProxy

class SettingAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.Setting._meta.fields]
  class Meta:
    model = models.Setting

class SchedulerAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.Scheduler._meta.fields]
  class Meta:
    model = models.Scheduler
  def get_form(self, request, obj=None, **kwargs):
    form = super(SchedulerAdmin, self).get_form(request, obj, **kwargs)
    #form.base_fields['schedule'].widget.attrs['style'] = 'width: 45em;'
    form.base_fields['schedule'].widget.attrs['style'] = 'width: 80%;'
    return form

class ErrorsAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.Errors._meta.fields]
  class Meta:
    model = models.Errors

class CityAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.City._meta.fields]
  class Meta:
    model = models.City

class GroupAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.Group._meta.fields]
  class Meta:
    model = models.Group

class GroupTaskAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.GroupTask._meta.fields]
  class Meta:
    model = models.GroupTask

class GroupLogAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.GroupLog._meta.fields]
  class Meta:
    model = models.GroupLog

class CommonInfoAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.CommonInfo._meta.fields]
  class Meta:
    model = models.CommonInfo

class CommonInfoHistoryAdmin(admin.ModelAdmin):
  list_display = [field.name for field in models.CommonInfoHistory._meta.fields]
  class Meta:
    model = models.CommonInfoHistory

admin.site.register(models.Proxy, ProxyAdmin)
admin.site.register(models.Proxy1, Proxy1Admin)
admin.site.register(models.UsedProxy, UsedProxyAdmin)
admin.site.register(models.Setting, SettingAdmin)
admin.site.register(models.Scheduler, SchedulerAdmin)
admin.site.register(models.Errors, ErrorsAdmin)
admin.site.register(models.City, CityAdmin)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.GroupTask, GroupTaskAdmin)
admin.site.register(models.GroupLog, GroupLogAdmin)
admin.site.register(models.CommonInfo, CommonInfoAdmin)
admin.site.register(models.CommonInfoHistory, CommonInfoHistoryAdmin)

