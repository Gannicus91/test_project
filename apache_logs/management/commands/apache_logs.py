from django.core.management.base import BaseCommand
import requests
import re
from tqdm import tqdm
import math
from datetime import *
from apache_logs.models import ApacheLog
import os
import warnings


class Command(BaseCommand):
    help = ''
    path = 'logs.bin'

    @staticmethod
    def get_data(url):
        """получить данные по URL и сохранить в файл"""
        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1048576
            with open(Command.path, 'wb') as file:
                for data in tqdm(response.iter_content(chunk_size=block_size),
                                 total=math.ceil(total_size // block_size),
                                 unit='KB', unit_scale=True, desc="Downloading data"):
                    file.write(data)
                wrote = file.tell()
            if total_size != 0 and wrote != total_size:
                return 0
            return 1
        except Exception as e:
            print(e)
            return 0

    @staticmethod
    def processing():
        """сохранение логов в бд"""
        with open(Command.path, 'rt') as f:
            r"""
            регулярное выражение задает следующий шаблон            
            (ip) (?:) (?:) [(дата и время) (часовой пояс)] "(HTTP method) \(?:) (?:)\" 
            (статус ответа) (размер ответа) "(источник)" (?:) "(?:)"
            ?: - игнорируемая группа
            доступ к необходимой группе осуществляется через match[номер группы]. Группы нумеруются с 1
            """
            reg = r'(\S+) (?:\S+) (?:\S+) \[((?:[^:]+):(?:\d+:\d+:\d+)) ([^\]]+)\] \"(\S+) (?:.*?) (?:\S+)\"' \
                  r' (\S+) (\S+) \"(.*?)\" \"(?:.*?)\" \"(?:.*?)\"'
            obj_list = []
            for log in tqdm(f.readlines(), unit_scale=True, desc="Processing data"):
                match = re.search(reg, log) #получили match-объект с интересующими группами

                if match is None:
                    continue

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

                obj_list.append(ApacheLog(ip=ip, date=date_time, tz=tz, method=method,
                                          referer=referer, status=status, resp_size=resp_size))
                if len(obj_list) == 999: #sqlite позволяет сохранить максимум 999 объктов за раз
                    with warnings.catch_warnings(): #игнорируем предупреждения о таймзонах
                        warnings.simplefilter("ignore")
                        ApacheLog.objects.bulk_create(obj_list)
                    obj_list = []

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ApacheLog.objects.bulk_create(obj_list)

        os.remove(Command.path)

    def handle(self, *args, **options):
        if Command.get_data(options['url']):
            Command.processing()

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            action='store',
            type=str,
            default=False,
            help='ссылка на файл с логами apache'
        )
