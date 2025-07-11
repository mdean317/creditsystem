from django.contrib import admin

# Register your models here.
from .models import CreditPackage, Practice, CreditTransaction
admin.site.register(CreditPackage)
admin.site.register(Practice)
admin.site.register(CreditTransaction)

