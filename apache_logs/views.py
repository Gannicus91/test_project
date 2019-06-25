from django.shortcuts import render
from django.views import generic
from .models import ApacheLog
from django.shortcuts import HttpResponse, HttpResponseRedirect
import openpyxl
from django.db.models import *


def redirect_view(request):
    return HttpResponseRedirect("/list")


class LogsView(generic.TemplateView):
    template_name = 'logs.txt'


class ApacheLogListView(generic.ListView):
    model = ApacheLog
    paginate_by = 50
    queryset = ApacheLog.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q', '')
        if query is not '':
            founded = qs.filter(Q(ip__icontains=query) |
                                Q(date__year__icontains=query) |
                                Q(date__month__icontains=query) |
                                Q(date__day__icontains=query) |
                                Q(method__icontains=query) |
                                Q(referer__icontains=query) |
                                Q(status__icontains=query) |
                                Q(resp_size__icontains=query)
                                )
            self.queryset = founded
        return self.queryset

    def get(self, request, **kwargs):
        if request.GET.get('download', False):
            return ApacheLogListView.download(request, self.get_queryset())
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ApacheLogListView, self).get_context_data(**kwargs)
        logs = self.queryset

        resp_sum = logs.aggregate(Sum('resp_size'))['resp_size__sum']
        methods_count = logs.values_list('method').annotate(
            methods_count=Count('method')).distinct().order_by('-methods_count')
        unique_ips = logs.values_list('ip').annotate(ip_count=Count('ip')).distinct().order_by('-ip_count')
        top_ips = unique_ips[:10]

        context['methods'] = methods_count
        context['top'] = top_ips
        context['ip_set_count'] = len(unique_ips)
        context['resp_sum'] = resp_sum
        context['q'] = self.request.GET.dict().get('q', '') #передаем в шаблон запрос поиска, чтобы пагинация учитывала поиск
        return context

    @staticmethod
    def download(request, queryset):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="data.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'ApacheLogs'

        columns = ['pk', 'IP', 'Date', 'Time zone' 'Method', 'Referer', 'Status', 'Response size', ]

        ws.append(columns)

        rows = queryset.values_list('pk', 'ip', 'date', 'tz', 'method', 'referer', 'status', 'resp_size')

        for row in rows:
            ws.append(row)

        wb.save(response)
        return response


