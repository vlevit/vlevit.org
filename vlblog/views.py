from django.http import HttpResponse

import scanner


def scan(request):
    scanner.scan()
    return HttpResponse('See log', content_type="text/plain")
