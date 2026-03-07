from django.contrib import admin
from .models import DataSource, Report, ChartImage

admin.site.register(DataSource)
admin.site.register(Report)
admin.site.register(ChartImage)
