from django.contrib import admin

# Register your models here.
from .models import CreditPackage, PracticeCredit, CreditTransaction, Practice

admin.site.register(CreditPackage)
admin.site.register(Practice)
admin.site.register(CreditTransaction)
admin.site.register(PracticeCredit)



