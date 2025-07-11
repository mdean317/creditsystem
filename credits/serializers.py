from rest_framework import serializers 
from .models import CreditPackage, CreditTransaction, PracticeCredit

class CreditPackageSerializer(serializers.ModelSerializer): 
    class Meta:
        model = CreditPackage 
        fields = "__all__"

'''  
At first I created serializers using django's built in restful capabilities, before diving more
into Django's async capabilities

class PracticeSerializer(serializers.ModelSerializer): 
    class Meta:
        model = PracticeCredit
        fields = "__all__"

class PracticeBalanceSerializer(serializers.ModelSerializer): 
    class Meta:
        model = PracticeCredit
        fields = ['balance']

class CreditTransactionSerializer(serializers.ModelSerializer): 
    class Meta:
        model = CreditTransaction 
        fields = "__all__"
'''
