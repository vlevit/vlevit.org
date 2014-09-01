import logging

from django.conf import settings


logger = logging.getLogger(__name__)

geodb_reader = None

if not settings.DEBUG:
    import geoip2.database
    import geoip2.errors

    try:
        geodb_reader = geoip2.database.Reader(settings.GEODB)
    except Exception:
        logger.exception("error reading geodatabase: %s", settings.GEODB)


def vlblog_processor(request):
    country = None
    if geodb_reader:
        try:
            country = geodb_reader.country(
                request.META['REMOTE_ADDR']).country.iso_code
        except geoip2.errors.GeoIP2Error:
            logger.exception("geoip error")
    return {'country': country}
