from django.db import models


class ApacheLog(models.Model):
    ip = models.GenericIPAddressField()
    date = models.DateTimeField()
    tz = models.SmallIntegerField()
    method = models.CharField(max_length=40)
    referer = models.URLField(blank=True, null=True)
    status = models.PositiveSmallIntegerField()
    resp_size = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return str(self.date)
