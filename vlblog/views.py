from django.http import HttpResponse

import scanner


def scan(request):
    report = scanner.scan()
    return HttpResponse(report, content_type="text/plain")
