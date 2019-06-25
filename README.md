# test_project
Проект реализует парсинг логов apache сервера, их обработку и хранение.
***
## Развертка, настройка и запуск проекта
### Загрузка проекта
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

### Настройка базы данных
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
### Запуск проекта на локальной машине

Выполните `python manage.py runserver`. В консоли появится сообщение
```bash
System check identified no issues (0 silenced).
June 23, 2019 - 18:23:42
Django version 2.2.2, using settings 'test_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Docker
Вы можете запустить проект с настройками по умолчанию, выполнив команды:
```bash
docker-compose run web python manage.py makemigrations
docker-compose run web python manage.py migrate
docker-compose up
```
### Сбор логов
Используйте команду `python manage.py get_logs <url>` чтобы собрать логи:
```bash
python manage.py get_logs http://www.almhuette-raith.at/apache-log/access.log
```
***
## Документация
### Model ApacheLog
Модель ApacheLog содержит основную информацию о логе: <br>
ip - Адрес IPv4 или IPv6 в виде строки<br>
date - дата и время запроса<br>
tz - целое число, часовой пояс<br>
method - HTTP-метод из заголовка запроса<br>
referer - URL источника запросам<br>
status - статусный код ответа<br>
resp_size - размер ответа в байтах<br>
### Management command get_logs
Команде get_logs на вход дается URL, по которому собираются логи
Класс Command содержит следующие методы
#### create_file
Параметры: path - путь к файлу;<br>
Создает временный файл, в который записываются логи.
#### remove_file
Параметры: path - путь к файлу;<br>
Удаляет временный файл.
#### save_data
Параметры: obj_list - список, содержащий объекты модели ApacheLog;<br>
Сохраняет данные в бд.
#### get_log_object_from_match
Параметры: match - macth-объект, группы которого будут полями объекта;<br>
Создает объект модели ApacheLog из macth-объекта
#### get_data
Параметры: url - ссылка на ресурс с логами;<br>
Получет и обрабатывает данные содержащиеся в url
### ApacheLogListView
Наследуется от generic.ListView. Реализует поиск, обработку и представление данных о логах. Также через статический метод download осуществляет экспорт в xlsx.
