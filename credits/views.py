from rest_framework import generics
from datetime import datetime
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from .serializers import CreditPackageSerializer
from .models import CreditPackage, Practice, CreditTransaction, PracticeCredit, TRANSACTION_TYPES, TYPE_PURCHASE
from .exceptions import CreditCardError
import json
import random
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from asgiref.sync import sync_to_async


'''Use async def methods (e.g., async def get(self, request)) inside your API views. '''
'''Use Django’s asynchronous ORM methods (aget, acreate, aupdate, adelete, etc.) instead of their synchronous counterparts.'''

async def credit_package_List(request):
    """View for listing all packages"""
    
    # This path only responds to POST requests
    if request.method == "GET":

        # Get the queryset of packages to display
        queryset = CreditPackage.objects.all().order_by("id").aiterator()

        packages=[]

        async for package in queryset:
            packages.append({
                    "id": package.id,
                    "name": package.name,
                    "credit_amount": package.credit_amount,
                    "price_cents": package.price_cents,
                    "is_active": package.is_active,
                    "description": package.updated_at,

            })

        return JsonResponse({
            "packages": packages,
        })


'''CSRF used just for testing!!'''
@csrf_exempt 
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

            def get_transaction_data(package, payment_type, last_four):
                '''Mock Payment Processing'''
                rand_int = random.randint(1, 5)

                if rand_int == 5:
                    '''Payment failed'''

                    status = 'fail' 
                    # Craft information string
                    info = f"Purchase attempt of {package.name} on {timezone.now()} using {payment_type}"
                    if payment_type == "credit_card":
                                info += f" ending with {last_four} "
                    info += " failed."
                    credits_to_add = 0
                    
                else:
                    '''Payment succeeded'''

                    status = 'success'
                    # Craft information string
                    info = f"Purchase of {package.name} on {timezone.now()} using {payment_type}"
                    if payment_type == "credit_card":
                                info += f" ending with {last_four}"
                    info += " succeeded."
                    credits_to_add = package.credit_amount

                return(status, credits_to_add, info)

            # Get needed transaction data, basedon success fail. 
            status, credits_to_add, info = get_transaction_data(package, payment_type, last_four)
            metadata = {"status": status, "type":TRANSACTION_TYPES[TYPE_PURCHASE], "additional information": info}
            
            @sync_to_async(thread_sensitive=True)
            def perform_async_atomic_transaction(practice_id, credits_to_add, package, metadata):
                with transaction.atomic():
                    
                    practice = Practice.objects.filter(id=practice_id).first()
        
                    PracticeCredit.objects.filter(practice=practice).update(balance=F('balance') + credits_to_add)
                    new_balance = PracticeCredit.objects.filter(practice=practice).values_list("balance", flat=True).first()
                    
                    # Create transaction record
                    credit_transaction = CreditTransaction(
                        practice=practice,
                        amount=credits_to_add,
                        transaction_type=TYPE_PURCHASE,
                        package=package,
                        metadata=metadata
                        )

                    credit_transaction.save()  
                    return(credit_transaction.id, new_balance, credit_transaction.reference_id)

            transaction_id, new_balance, reference_id  = await perform_async_atomic_transaction(practice_id, credits_to_add, package, metadata)

            return JsonResponse({
                    "transaction_id": transaction_id,
                    "status": status ,
                    "credits_added": credits_to_add,
                    "new_balance": new_balance,
                    "receipt_url": f"/api/credits/receipts/{reference_id}/"
                    })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

async def credit_balance(request):
    """View for checking a practice's credit balance"""

    # Get practice id from url 
    str_practice_id = request.GET.get('practice_id')

    if not str_practice_id:
        return JsonResponse({"error": "practice_id is required"}, status=400)

    try:
        practice_id = int(str_practice_id)

    except ValueError:
        return JsonResponse({"error": "practice_id must be an integer"}, status=400)
    
    try:
   
        # Get credit info by practice id
        practice_credit = await PracticeCredit.objects.aget(practice__id=practice_id)
        
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