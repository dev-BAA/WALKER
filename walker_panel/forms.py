from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import *
from walker_panel.models import City, Group, GroupTask, Setting


class SignUpForm(UserCreationForm):
    username = EmailField(max_length=254, help_text='Required. Inform a valid email address.', label='Email')

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class GTaskForm(ModelForm):
    owner = CharField(widget=HiddenInput(), required=False)
    name = CharField(widget=HiddenInput(), required=False)
    id = IntegerField(widget=HiddenInput(), required=False)
    target_group = ModelChoiceField(widget=HiddenInput(), queryset = Group.objects.all())

    search_query = CharField(widget=TextInput(attrs={'style': 'width:450px'}), label='Поисковый запрос', help_text='*по этому запросу мы будем искать сайт в Яндексе')
    launches_per_day = IntegerField(widget=TextInput(attrs={'style': 'width:50px'}), label='Количество запусков в день', help_text='*максимальное количество запусков в день (0 — без ограничений)')

    class Meta:
        model = GroupTask
        fields = ['name', 'id', 'target_group', 'search_query', 'launches_per_day']
        widgets = {
            'name': TextInput(attrs={'name': 'name'}),
        }

class GroupForm(ModelForm):
    name = CharField(widget=HiddenInput(), required=False)
    id = IntegerField(widget=HiddenInput(), required=False)
    group_name = CharField(widget=TextInput(attrs={'style': 'width:400px'}), label='Имя группы')
    target_url = CharField(widget=TextInput(attrs={'style': 'width:400px'}), label='Целевой сайт', help_text=f'*на этом сайте мы будем проводить больше всего времени и выполнять целевые действия')
    competitor_sites = CharField(label="Сайты конкурентов (в столбик)", widget=Textarea(attrs={}), help_text='*эти сайты мы будем быстро покидать', required=False)
    city = CharField(label='Населённый пункт')

    class Meta:
        model = Group
        fields = ['name', 'id', 'group_name', 'target_url', 'city', 'proxy_list']
        widgets = {
            'city': TextInput(attrs={'name': 'city'}),
        }

class ProxyForm(Form):
    proxies = CharField(label='Список прокси', help_text='Прокси в формате host:port[:username:password]. Пока поддерживаются только HTTP-прокси без авторизации.',
                        widget=Textarea(attrs={'placeholder': 'host:port[:username:password]', 'rows': 5}))

    class Meta:
        fields = ['proxies']

class SettingForm(ModelForm):
    stalker_page_range = IntegerField(widget=TextInput(attrs={'style': 'width:50px'}), label='Глубина поиска', help_text='страниц выдачи поиска Яндекс')
    workers_time_start = IntegerField(widget=TextInput(attrs={'style': 'width:50px'}), label='Начать задачи в', help_text='часов утра')
    workers_time_end = IntegerField(widget=TextInput(attrs={'style': 'width:50px'}), label='Завершить задачи в', help_text='часов вечера')
    rucaptcha_key = CharField(widget=TextInput(attrs={'style': 'width:350px'}), label='Рукапча key', help_text='api key для сервиса Рукапча')
    email_admin = CharField(widget=TextInput(attrs={'style': 'width:250px'}), label='Почта администратора', help_text='на этот адрес будут высылаться ошибки выполнения бота')
    email_dev = CharField(widget=TextInput(attrs={'style': 'width:250px'}), label='Почта разработчика', help_text='на этот адрес будут высылаться ошибки выполнения бота')

    class Meta:
        model = Setting
        fields = ['workers_time_start', 'workers_time_end', 'stalker_page_range', 'rucaptcha_key', 'email_admin', 'email_dev']

