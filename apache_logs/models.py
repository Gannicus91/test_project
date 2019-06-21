from django.db import models


class ApacheLog(models.Model):
    ip = models.GenericIPAddressField(verbose_name='IP')
    date = models.DateTimeField(verbose_name='Дата')
    tz = models.SmallIntegerField(verbose_name='Часовой пояс')
    method = models.CharField(max_length=40, verbose_name='HTTP метод')
    referer = models.URLField(blank=True, null=True, verbose_name='Источник')
    status = models.PositiveSmallIntegerField(verbose_name='Статус ответа')
    resp_size = models.PositiveIntegerField(blank=True, null=True, verbose_name='Размер ответа')

    def __str__(self):
        return str(self.date)
