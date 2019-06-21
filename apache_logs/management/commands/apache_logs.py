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
            wrote = 0
            with open(Command.path, 'wb') as f:
                for data in tqdm(response.iter_content(chunk_size=block_size),
                                 total=math.ceil(total_size // block_size),
                                 unit='KB', unit_scale=True, desc="Downloading data"):
                    wrote = wrote + len(data)
                    f.write(data)
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
            reg = r'(\S+) (\S+) (\S+) \[((?:[^:]+):(?:\d+:\d+:\d+)) ([^\]]+)\] \"(\S+) (.*?) (\S+)\"' \
                  r' (\S+) (\S+) \"(.*?)\" \"(.*?)\" \"(.*?)\"'
            obj_list = []
            for log in tqdm(f.readlines(), unit_scale=True, desc="Processing data"):
                m = re.search(reg, log) #получили match-объект с интересующими группами

                if m is None:
                    continue

                date_time = datetime.strptime(m[4], "%d/%b/%Y:%H:%M:%S")
                tz = int(m[5][:3])

                if m[11] == '-':
                    referer = None
                else:
                    referer = m[11]

                if m[10] == '-':
                    resp_size = None
                else:
                    resp_size = int(m[10])

                obj_list.append(ApacheLog(ip=m[1], date=date_time, tz=tz, method=m[6],
                                          referer=referer, status=m[9], resp_size=resp_size))
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
