import logging

from django.conf import settings

if not settings.DEBUG:
    import geoip2.database
    import geoip2.errors


logger = logging.getLogger(__name__)

geodb_reader = None


def get_geodb_reader():
    try:
        geodb_reader = geoip2.database.Reader(settings.GEODB)
    except Exception:
        logger.exception("geoip db read error: %s", settings.GEODB)
        geodb_reader = None
    return geodb_reader


def vlblog_processor(request):
    global geodb_reader
    country = None
    if not settings.DEBUG:
        for i in range(2):
            # if geoip error or the first call (re-)open the database
            # (error may occur if geoip database file was updated)
            if not geodb_reader:
                geodb_reader = get_geodb_reader()
            if geodb_reader:
                try:
                    country = geodb_reader.country(
                        request.META['REMOTE_ADDR']).country.iso_code
                except geoip2.errors.AddressNotFoundError:
                    pass
                except Exception:  # must be unhandled exception inside geoip2
                    logger.exception("country code read error")
                    try:
                        geodb_reader.close()
                    except Exception:
                        logger.exception("geoip db close error")
                    geodb_reader = None
                    continue
            break
    return {'country': country}
