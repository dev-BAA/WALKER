# Серфинг целевых сайтов в Яндекс поиске

В данном проекте реализован серфинг целевых сайтов в Яндекс поиске, с целью накрутки посещений.

## Установка

- ОС сервера **Ubuntu 18.04**
- установка Python  
  sudo apt install python3.7 python3-venv python3.7-venv  
  sudo apt install python3.7-dev  
  sudo apt install build-essential -y  
  sudo apt install libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev -y  
  sudo apt-get install redis-server  
- установка Google Chrome  
  sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add  
  sudo echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list  
  sudo apt-get -y update  
  sudo apt-get -y install google-chrome-stable  
- установка PostgreSQL  
  sudo apt-get install postgresql postgresql-server-dev-10  
  sudo -u postgres psql postgres  
  \password postgres  
  PASSWORD  
- настройка PostgreSQL  
  create user USERNAME with password 'PASSWORD';  
  alter role USERNAME set client_encoding to 'utf8';  
  alter role USERNAME set default_transaction_isolation to 'read committed';  
  alter role USERNAME set timezone to 'Europe/Moscow';  
  create database django_db owner USERNAME;  
  \q  
- установка виртуального окружения  
  python3.7 -m venv NAMEVENV  
  source NAMEVENV/bin/activate  
  pip install django  
  pip install psutil  
  pip install psycopg2  
  pip install psycopg2-binary  
  pip install selenium  
  pip install -r requirements.txt  
- старт проекта  
  django-admin startproject site_walker  
  django-admin startproject site_walker /root/site_walker  
  python3.7 manage.py runserver  
  python3.7 manage.py startapp walker_panel  
  python3.7 manage.py makemigrations  
  python3.7 manage.py migrate  
  python3.7 manage.py createsuperuser  
- скачать драйвер и установить права  
  Скачать с сайта https://sites.google.com/a/chromium.org/chromedriver/downloads , версия драйвера должна соответсвовать версии установленного Google Chrome.  
  chmod u+x chromedriver  
- установка python бота как сервиса  
  systemctl enable walker.service  
  systemctl daemon-reload  
  sudo service walker start  
  service walker status  
  walker.service:  
  [Unit]  
  Description=walker  
  
  [Service]  
  Type=idle  
  ExecStart=/root/site_walker/myvenv/bin/python3.7 /root/site_walker/manage.py runscript bot  
  WorkingDirectory=/root/site_walker/  
  Restart=always  
  
  
  [Install]  
  Alias=walker  
  WantedBy=default.target  

## Настройки

