from django.contrib import admin
from django.contrib.admin import site, ModelAdmin
from .models import Accounts_list
from .models import Accounts
from .models import *
# Register your models here.
admin.site.register(Accounts_list)
admin.site.register(Accounts)
admin.site.register(Transac)
admin.site.register(Scheme)
admin.site.register(Scheme_count)