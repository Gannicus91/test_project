from django.core.management.base import BaseCommand
import requests
import re
from tqdm import tqdm
import math
from datetime import *
from apache_logs.models import ApacheLog
import os
import warnings
import time as tm


class Command(BaseCommand):
    help = ''
    path = 'logs.bin'
    pattern = r'(\S+) (?:\S+) (?:\S+) \[((?:[^:]+):(?:\d+:\d+:\d+)) ([^\]]+)\] \"(\S+) (?:.*?) (?:\S+)\"' \
              r' (\S+) (\S+) \"(.*?)\" \"(?:.*?)\" \"(?:.*?)\"'

    @staticmethod
    def get_data(url):
        """загрузка и обработка данных"""
        try:
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
            cut = ['', '']
            for data in tqdm(response.iter_content(chunk_size=block_size),
                             total=math.ceil(total_size // block_size),
                             unit='KB', unit_scale=True, desc="Downloading & processing the data"):
                data = data.decode('utf-8').split('\n')
                cut[1] = data.pop()
                if re.fullmatch(Command.pattern, cut[0]):
                    Command.process([cut[0]], obj_list)
                else:
                    Command.process([cut[0] + data.pop(0)], obj_list)
                Command.process(data, obj_list)
                cut[0] = cut[1]
                wrote += len(data)
            Command.save_data(obj_list)
            if total_size != 0 and wrote != total_size:
                return 0
            return 1
        except Exception as e:
            print(e)
            return 0

    @staticmethod
    def process(data, obj_list):
        for log in data:
            match = re.search(Command.pattern, log)  # получили match-объект с интересующими группами

            if match is None:
                print(log)
                continue

            obj_list.append(Command.get_log_object_from_match(match))
            if len(obj_list) == 999:  # sqlite позволяет сохранить максимум 999 объктов за раз
                Command.save_data(obj_list)
                obj_list = []

    @staticmethod
    def get_log_object_from_match(match):
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

    @staticmethod
    def create_file(path):
        f = open(path, 'w')
        f.close()

    @staticmethod
    def remove_file(path):
        os.remove(path)
