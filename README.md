# test_project
Проект реализует парсинг логов apache сервера, их обработку и хранение.
***
## Загрузка проекта
Сначала необходимо клонировать репозиторий на локальную машину:
```bash
git clone git@github.com:Gannicus91/test_project.git
```

Создайте и активируйте виртуальное окружение:
```bash
py -m venv venv
venv\Scripts\activate
```

Установите необходимые библиотеки:
```bash
pip install -r requirements.txt
```
***
## Настройка базы данных
В `settings.py` укажите используемую СУБД. По умолчанию - `sqlite`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

Выполните миграции с помощью команд: `python manage.py makemigrations` `python manage.py migrate`
***
## Запуск проекта на локальной машине

Выполните `python manage.py runserver`. В консоли появится сообщение
```bash
System check identified no issues (0 silenced).
June 23, 2019 - 18:23:42
Django version 2.2.2, using settings 'test_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Используйте команду `python manage.py apache_logs <url>` чтобы собрать логи:
```bash
python manage.py apache_logs http://www.almhuette-raith.at/apache-log/access.log
```
