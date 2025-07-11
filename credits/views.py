from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from django.db.models import F
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from .serializers import CreditPackageSerializer, PracticeSerializer, CreditTransactionSerializer, PracticeBalanceSerializer
from .models import CreditPackage, Practice, CreditTransaction, PracticeCredit
from .exceptions import CreditCardError
import json
import random
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urlencode


'''Use async def methods (e.g., async def get(self, request)) inside your API views. '''
'''Use Django’s asynchronous ORM methods (aget, acreate, aupdate, adelete, etc.) instead of their synchronous counterparts.'''

class CreditPackageList(generics.ListAPIView):
    serializer_class = CreditPackageSerializer 

    async def get_queryset(self):
        return CreditPackage.objects.all().order_by('name')

async def purchase_credits(request):
    """View for buying more credits(POST)"""

    # This path only responds to POST requests
    if request.method == "POST":


        try:

            data = json.loads(request.body) # This is synchronous, but it is the best option I found. 
            practice_id = data.get('practice_id')
            package_id = data.get('package_id')
            payment_method = data.get('payment_method')
            payment_type = payment_method.get('type') if payment_method else None
            last_four = payment_method.get('last_four') if payment_method else None

            package = await CreditPackage.objects.filter(id=package_id).afirst() 
            
            if package is None:
                return JsonResponse({"error": "Invalid package ID"}, status=404)

            '''Mock Payment Processing'''
            rand_int = random.randint(1, 5)

            async with transaction.atomic():
                if rand_int == 5:
                    '''Payment failed'''

                    status = "fail"
                    # Craft information string
                    info = f"Purchase attempt of {package.name} on {timezone.now()} using {payment_type}"
                    if payment_type == "credit_card":
                                info += f" ending with {last_four} "
                    info += " failed."
                    
                    credits_added = 0
                
                else:
                    '''Payment succeeded'''

                    status = "success"
                    # Craft information string
                    info = f"Purchase of {package.name} on {timezone.now()} using {payment_type}"
                    if payment_type == "credit_card":
                                info += f" ending with {last_four}"
                    info += " succeeded."

                    credits_added = package.credit_amount
                    await PracticeCredit.objects.filter(id=practice_id).aupdate(balance=F('balance') + package.credit_amount)
                  
                new_balance = await PracticeCredit.objects.filter(id=practice_id).values_list("balance", flat=True).afirst()
                
                 # Create successfull transaction record
                transaction = CreditTransaction(
                    practice=practice_id,
                    amount=credits_added,
                    transaction_type="PURCHASE",
                    metadata= {"status": status, "type":"Purchase", 
                                "additional information": info}
                    )

                await transaction.asave()  

                return JsonResponse({
                        "transaction_id": transaction.reference_id,
                        "status": status ,
                        "credits_added": credits_added,
                        "new_balance": new_balance,
                        "receipt_url": "/api/credits/receipts/{transaction.reference_id}/"
                        })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

async def credit_balance(request):
    """View for checking a practice's credit balance"""

    # Get practice id from url 
    practice_id = int(request.GET.get('practice_id'))
    
    # If couldn't get paramter, respond with the error
    if not practice_id:
        return JsonResponse({"error": "practice_id is required"}, status=400)
    
    try:

        # Get credit info by practice id
        practice_credit = await PracticeCredit.objects.aget(practice_id=practice_id)
        
        # Calculate estimated remaining communications
        '''These should be seprate functions'''
        avg_sms_cost = 2  # credits per SMS
        avg_voice_cost = 5  # credits per voice call
        
        return JsonResponse({
            "practice_id": practice_id,
            "current_balance": practice_credit.balance,
            "last_purchase": await practice_credit.last_purchase_date(),
            "estimated_remaining_sms": practice_credit.balance // avg_sms_cost,
            "estimated_remaining_voice": practice_credit.balance // avg_voice_cost
        })
    
    except PracticeCredit.DoesNotExist:
        return JsonResponse({"error": "Practice not found"}, status=404)

async def transaction_history(request):
    practice_id = request.GET.get("practice_id")

    # If couldn't get paramter, respond with this error
    if not practice_id:
        return JsonResponse({"error": "practice_id is required"}, status=400)
    
    # Set up paginataion query parameters 
    page = int(request.GET.get("page", 1))
    page_size = 20
    offset = (page - 1) * page_size
    limit = offset + page_size

    # Set up paginataion url building parameters and function
    base_url = request.build_absolute_uri(request.path)
    query_params = request.GET.dict()
    query_params.pop("page", None)

    def build_page_url(page_number):
        return f"{base_url}?{urlencode({**query_params, 'page': page_number})}"
    
    # Get the queryset transactions to display
    queryset = (
        CreditTransaction.objects
        .filter(practice_id=practice_id)
        .order_by("-created_at")
    )

    total = await queryset.acount()

    # Select values to show taking pagination into account
    transactions = queryset.values(
        "id", "transaction_type", "amount", "created_at",
        "package__id", "package__name"
    )[offset:limit].aiterator()
   
    results = []

    # For each transaction, parse into json based on whether it is a purchase or a campaign 
    async for transaction in transactions:
        if transaction["transaction_type"] == "PURCHASE":
            results.append({
                "id": transaction["id"],
                "type": transaction["transaction_type"],
                "amount": int(transaction["amount"]),
                "timestamp": transaction["created_at"],
                "package": {
                     "id": transaction["package__id"],
                     "name": transaction["package__name"],
                }
            })
        else:
           
            results.append({
                "id": transaction["id"],
                "type": transaction["transaction_type"],
                "amount": int(transaction["amount"]),
                "timestamp": transaction["created_at"],
                "reference": "" #reference to be implmented - wasn't sure want to put here and deprioritized
            })
    
    pagination = {
        "next": build_page_url(page + 1) if limit < total else None,
        "previous": build_page_url(page - 1) if page > 1 else None
    }
    
    return JsonResponse({
        "transactions": results,
        "pagination": pagination,
    })