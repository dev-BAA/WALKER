# Серфинг целевых сайтов в Яндекс поиске

В данном проекте реализован серфинг целевых сайтов в Яндекс поиске, с целью накрутки посещений.

## Установка

- ОС сервера **Ubuntu 18.04**
- установить общие пакеты  
  sudo apt update  
  sudo apt upgrade  
  sudo apt install net-tools mc openssh-server curl  
- установить Python  
  sudo apt install python3.7 python3-venv python3.7-venv  
  sudo apt install python3.7-dev  
  sudo apt install build-essential -y  
  sudo apt install libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev -y  
  sudo apt-get install redis-server  
- установить Google Chrome  
  sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add  
  sudo echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list  
  sudo apt-get -y update  
  sudo apt-get -y install google-chrome-stable  
- установить PostgreSQL  
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


## Настройки

