try:
    from django.conf.urls import patterns
except ImportError:
    from django.conf.urls.defaults import patterns


urlpatterns = patterns(
    '',
    (r'^$', 'smoketest.views.index'),
)
