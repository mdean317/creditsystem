"""
URL configuration for CreditSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(),  name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from credits import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/credits/packages/', views.credit_package_List, name='list_credit_packages'), 
    path('api/credits/purchase/', views.purchase_credits, name='purchase_credits'), 
    path('api/credits/balance/', views.credit_balance, name='practice_balance'), 
    path('api/credits/transactions/', views.transaction_history, name='practice_transactions_list'), 
    #path('api/credits/transactions/buySMS', views..as_view(), name=''), 
    #path('api/credits/transactions/buyVC', views..as_view(), name=''), 
]