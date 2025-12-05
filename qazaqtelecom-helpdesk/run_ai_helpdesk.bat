@echo off
REM Путь к Python из виртуального окружения
set PYTHON=d:\qazaqtelecom-helpdesk\.venv\Scripts\python.exe

cd /d d:\qazaqtelecom-helpdesk

echo === Применение миграций ===
%PYTHON% manage.py makemigrations
%PYTHON% manage.py migrate

echo === Создание демо-данных ===
%PYTHON% manage.py create_init_data

echo === Запуск сервера разработки ===
%PYTHON% manage.py runserver

pause