from django.core.management.base import BaseCommand
import requests
import re
from tqdm import tqdm
import math
from datetime import *
from apache_logs.models import ApacheLog
import warnings
import time as tm


class Command(BaseCommand):
    help = 'собирает логи по указанному URL'
    pattern = r'(\S+) (?:\S+) (?:\S+) \[((?:[^:]+):(?:\d+:\d+:\d+)) ([^\]]+)\] \"(\S+) (?:.*?) (?:\S+)\"' \
              r' (\S+) (\S+) \"(.*?)\" \"(?:.*?)\" \"(?:.*?)\"'

    @staticmethod
    def get_data(url):
        try:
            """загрузка и обработка данных"""
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1048576 # считываем по 1мб
            r"""
            регулярное выражение задает следующий шаблон            
            (ip) (?:) (?:) [(дата и время) (часовой пояс)] "(HTTP method) \(?:) (?:)\" 
            (статус ответа) (размер ответа) "(источник)" (?:) "(?:)"
            ?: - игнорируемая группа
            доступ к необходимой группе осуществляется через match[номер группы]. Группы нумеруются с 1
            """
            obj_list = []
            wrote = 0
            cut = ['', ''] # первый элемент - часть строки считанная в прошлой итерации, второй - в этой
            for data in tqdm(response.iter_content(chunk_size=block_size),
                             total=math.ceil(total_size // block_size),
                             unit='KB', unit_scale=True, desc="Downloading & processing the data"):
                data = data.decode('utf-8').split('\n')
                cut[1] = data.pop() # запоминаем обрезанную строку для следующей итерации
                stuck = cut[0] + data.pop(0) # склеиваем обрезанные части строк
                if re.fullmatch(Command.pattern, cut[0]):
                    obj_list.append(Command.get_log_object(cut[0]))
                else:
                    if stuck:
                        obj_list.append(Command.get_log_object(stuck))
                Command.process(data, obj_list)
                cut[0] = cut[1] # обновляем cut для след. итерации
                wrote += len(data)
                Command.save_data(obj_list)
                obj_list = []
            if total_size != 0 and wrote != total_size:
                raise Exception("Something went wrong")
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def process(data, obj_list):
        for log in data:
            log_obj = Command.get_log_object(log)
            if log_obj:
                continue
            else:
                obj_list.append(log_obj)

    @staticmethod
    def get_log_object(log):
        match = re.search(Command.pattern, log)  # получили match-объект с интересующими группами
        if match is None:
            return False
        ip = match[1]
        date_time = datetime.strptime(match[2], "%d/%b/%Y:%H:%M:%S")
        tz = int(match[3][:3])
        method = match[4]
        status = match[5]
        if match[6] == '-':
            resp_size = None
        else:
            resp_size = int(match[6])
        if match[7] == '-':
            referer = None
        else:
            referer = match[7]
        return ApacheLog(ip=ip, date=date_time, tz=tz, method=method,
                         referer=referer, status=status, resp_size=resp_size)

    def handle(self, *args, **options):
        Command.start = tm.time()
        Command.get_data(options['url'])
        Command.end = tm.time()
        print(Command.end - Command.start)

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            action='store',
            type=str,
            default=False,
            help='ссылка на файл с логами apache'
        )

    @staticmethod
    def save_data(obj_list):
        with warnings.catch_warnings():  # игнорируем предупреждения о таймзонах
            warnings.simplefilter("ignore")
            ApacheLog.objects.bulk_create(obj_list)
