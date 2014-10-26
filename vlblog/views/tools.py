from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render

from utils import require_key
from vlblog import exporters, importers


@csrf_exempt
@require_key
def import_entries(request, what):
    force_reimport = False
    if 'force_reimport' in request.REQUEST:
        force_reimport = True
    if what in ('blog', 'all'):
        blog_importer = importers.BlogImporter(settings.BLOG_DIR)
        blog_importer.import_all(force_reimport=force_reimport)
    if what in ('pages', 'all'):
        pages_importer = importers.PagesImporter(settings.PAGES_DIR)
        pages_importer.import_all(force_reimport=force_reimport)
    return HttpResponse('See log', content_type="text/plain")


@csrf_exempt
@require_key
def export_gplus(request):
    if not settings.GPLUS_EXPORT:
        return HttpResponse("Google+ export is disabled in the config",
                            content_type="text/plain")
    exporter = exporters.GPlusExporter(settings.GPLUS_CREDENTIALS_FILE)
    inserted = exporter.export()
    return HttpResponse("Exported %d entries to Google+" % inserted)


def gplus_callback(request):
    if request.GET:
        request.session['gplus'] = request.GET
        return redirect(gplus_callback)
    else:
        response = request.session.pop('gplus', {})
        return render(request, 'gplus.html', dict(response=response))


def pingme(request):
    return HttpResponse('Thanks!', content_type="text/plain")


@require_key
def internal_error(request):
    raise Exception('Internal Error Test')
