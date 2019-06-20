from django.shortcuts import render
from django.views import generic
from .models import ApacheLog
from django.db.models import Q
from django.shortcuts import HttpResponse
import openpyxl

QUERY = ApacheLog.objects.all()


def redirect_view(request):
    return HttpResponseRedirect("/list")


class LogsView(generic.TemplateView):
    template_name = 'logs.txt'


class ApacheLogListView(generic.ListView):
    model = ApacheLog
    paginate_by = 50
    queryset = QUERY

    def get_queryset(self):
        global QUERY
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
        QUERY = self.queryset
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(ApacheLogListView, self).get_context_data(**kwargs)
        logs = self.queryset
        resp_size_list = [] #массив всех размеров ответа
        ip_set = set() #множество всех ip
        ip_set_size = 0 #размер множества
        ip_count_d = dict() #словарь типа {ip: кол-во, ...}
        """для http методов аналогично"""
        method_set = set()
        method_set_size = 0
        method_count_d = dict()

        for log in logs:
            if log.resp_size is not None:
                resp_size_list.append(log.resp_size)
            ip_set_size = ApacheLogListView.update_set(ip_set, ip_count_d, ip_set_size, log.ip)
            method_set_size = ApacheLogListView.update_set(method_set, method_count_d, method_set_size, log.method)

        resp_sum = sum(resp_size_list)

        ip_list = list(ip_count_d.items()) #получили список кортежей
        ip_list.sort(key=lambda l: l[1], reverse=True) #отсортировали по значению
        top_ips = dict()
        dp = 10 if len(ip_list) >= 10 else len(ip_list)
        for i, j in zip(ip_list, range(dp)): #сохранили первые 10 или меньше значений
            top_ips[i[0]] = i[1]
        q = self.request.GET.dict().get('q', '')
        context['methods'] = method_count_d
        context['top'] = top_ips
        context['ip_set_count'] = len(ip_set)
        context['resp_sum'] = resp_sum
        context['q'] = q #передаем в шаблон запрос поиска, чтобы при пагинации учитывался поиск
        return context

    @staticmethod
    def update_set(o_set, o_dict, o_set_size, key):
        """функция облегчает построение словаря типа {объект: кол-во объектов в списке, ...}"""
        o_set.add(key)
        if o_set_size < len(o_set):
            o_set_size += 1
            o_dict[key] = 1
        else:
            o_dict[key] += 1
        return o_set_size


def download(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="data.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'ApacheLogs'

    columns = ['pk', 'IP', 'Date', 'Time zone' 'Method', 'Referer', 'Status', 'Response size', ]

    ws.append(columns)

    rows = QUERY.values_list('pk', 'ip', 'date', 'tz', 'method', 'referer', 'status', 'resp_size')

    for row in rows:
        ws.append(row)

    wb.save(response)
    return response


