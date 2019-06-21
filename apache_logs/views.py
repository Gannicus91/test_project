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
        ip_count_d = dict() #словарь {ip: число запросов }
        method_count_d = dict() #словарь {method: число запросов }

        for log in logs:
            if log.resp_size is not None:
                resp_size_list.append(log.resp_size) #если размер передан сохраняем его в список
            ip_set.add(log.ip)
            ApacheLogListView.add_or_update(ip_count_d, log.ip)
            ApacheLogListView.add_or_update(method_count_d, log.method)

        resp_sum = sum(resp_size_list)

        ip_list = list(ip_count_d.items()) #получили список кортежей
        ip_list.sort(key=lambda l: l[1], reverse=True) #отсортировали по значению
        top_ips = dict()
        dp = 10 if len(ip_set) >= 10 else len(ip_set)
        for i, j in zip(ip_list, range(dp)): #сохранили первые 10 или меньше значений
            top_ips[i[0]] = i[1]
        q = self.request.GET.dict().get('q', '')
        context['methods'] = method_count_d
        context['top'] = top_ips
        context['ip_set_count'] = len(ip_set)
        context['resp_sum'] = resp_sum
        context['q'] = q #передаем в шаблон запрос поиска, чтобы пагинация учитывала поиск
        return context

    @staticmethod
    def add_or_update(o_dict, key):
        """если в словаре нет переданного ключа, то он добавляется со значением 1, 
        иначе увеличиваем значение по ключу на 1"""
        if o_dict.get(key, None) is None:
            o_dict[key] = 1
        else:
            o_dict[key] += 1


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


