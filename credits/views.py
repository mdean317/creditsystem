from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from .models import CreditPackage, Practice, CreditTransaction, PracticeCredit, TRANSACTION_TYPES, TYPE_PURCHASE, TYPE_SMS, TYPE_VOICE
from .exceptions import CorruptedPackage, PracticeDoesNotExist, PracticeCreditDoesNotExist
from .services import calc_SMS_pay_as_you_go_remaining, calc_VC_pay_as_you_go_remaining
import json
import random
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from asgiref.sync import sync_to_async

async def credit_package_List(request):
    """View for listing all packages"""
    
    # This path only responds to GET requests
    if request.method != "GET":

        return JsonResponse({"error": f"{request.method} method not allowed on this endpoint."}, status=405)

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
                "is_package_pay_as_you_go": package.is_package_pay_as_you_go,
                "description": package.description,

        })

    return JsonResponse({
        "packages": packages,
    })


'''CSRF used just for testing!!'''
@csrf_exempt 
async def purchase_credits(request):
    """View for buying more credits(POST)"""
    
    # This path only responds to POST requests
    if request.method != "POST":

        return JsonResponse({"error": f"{request.method} method not allowed on this endpoint."}, status=405)
    
    try:

        # get the parameters from the payload
        data = json.loads(request.body) # This is synchronous, but it is the best option I found. 
        practice_id = data.get('practice_id')
        package_id = data.get('package_id')
        payment_method = data.get('payment_method')
        payment_type = payment_method.get('type') if payment_method else None
        last_four = payment_method.get('last_four') if payment_method else None

        package = await CreditPackage.objects.aget(id=package_id)

        def perform_payment_and_prep_transaction_data(package, payment_type, last_four):
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

        # Get needed transaction data, based on success/fail. 
        status, credits_to_add, info = perform_payment_and_prep_transaction_data(package, payment_type, last_four)
        metadata = {"status": status, "type":TRANSACTION_TYPES[TYPE_PURCHASE], "additional information": info}
            
        @sync_to_async(thread_sensitive=True)
        def atomic_log_transaction(practice_id, credits_to_add, package, metadata):
            with transaction.atomic():
                ''' log transaction and update practice credit in db  in an atomic way'''

                # get practice object for transaction lof
                practice = Practice.objects.filter(id=practice_id).first()

                if not practice:
                    raise PracticeDoesNotExist(practice_id)
                
                # update prectice credit with new credits (make sure it exists)
                rows_updated = PracticeCredit.objects.filter(practice_id=practice_id).update(balance=F('balance') + credits_to_add)

                if rows_updated == 0:
                    raise PracticeCreditDoesNotExist(practice_id)
                
                new_balance = PracticeCredit.objects.filter(practice_id=practice_id).values_list("balance", flat=True).first()

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

        transaction_id, new_balance, reference_id  = await atomic_log_transaction(practice_id, credits_to_add, package, metadata)

        return JsonResponse({
                "transaction_id": transaction_id,
                "status": status ,
                "credits_added": credits_to_add,
                "new_balance": new_balance,
                "receipt_url": f"/api/credits/receipts/{reference_id}/"
                })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    except CreditPackage.DoesNotExist:
        return JsonResponse({"error": "Package not found"}, status=404)
    
    except PracticeCreditDoesNotExist as e:
        return JsonResponse({"error": str(e)}, status=404)
    
    except PracticeDoesNotExist as e:
        return JsonResponse({"error": str(e)}, status=404)

async def credit_balance(request):
    """View for checking a practice's credit balance"""

    # This path only responds to GET requests
    if request.method != "GET":
        
        return JsonResponse({"error": f"{request.method} method not allowed on this endpoint."}, status=405)
    
    # initiate variables
    estimated_remaining_SMS = 0
    estimated_remaining_VC = 0

    # Get practice id from url 
    str_practice_id = request.GET.get('practice_id')

    if not str_practice_id:
        return JsonResponse({"error": "practice_id is required"}, status=400)

    try:
        practice_id = int(str_practice_id)

    except ValueError:
        return JsonResponse({"error": "practice_id must be an integer"}, status=400)
    
    try:
   
        # Get practice credit info by practice id
        practice_credit = await PracticeCredit.objects.select_related('current_package').aget(practice_id=practice_id)
        is_pay_as_you_go = practice_credit.current_package.is_package_pay_as_you_go
        last_purchase_date = await practice_credit.last_purchase_date()

        # Calculate estimated remaining communications
        if is_pay_as_you_go:
            '''if practice is using a pay-at-you-go program'''
            '''TODO: address the event where practice bought several pay-as-you-go credits, so calculation shouldn't necessarily start from last purchase '''
            '''TODO: address the time limit on pay-as-you-go count (month for example) and count from the determined plan sstart date '''
        
            # get all SMS usage since last purchase
            sms_campaign_queryset = (CreditTransaction.objects
                                    .filter(practice_id=practice_id, transaction_type=TYPE_SMS, created_at__gt=last_purchase_date)
                                    .all()
                                    )
            
            # evaluate queryset asynchly and convert to list
            sms_campaigns = await sync_to_async(list)(sms_campaign_queryset)
            
            # estimated remaining SMS based on credit balance and package rate
            estimated_remaining_SMS = calc_SMS_pay_as_you_go_remaining(practice_credit.balance, sms_campaigns)
            
            # get all VC usage since last purchase
            voice_campaign_queryset = (CreditTransaction.objects
                                    .filter(practice_id=practice_id, transaction_type=TYPE_VOICE, created_at__gt=last_purchase_date)
                                    .all()
                                    )
            
            # evaluate queryset asynchly and convert to list
            voice_campaigns = await sync_to_async(list)(voice_campaign_queryset)

            # estimated remaining VC based on credit balance and package rate
            estimated_remaining_VC = calc_VC_pay_as_you_go_remaining(practice_credit.balance, voice_campaigns)
            

        else:

            if practice_credit.current_package.credit_per_SMS:

                # using the package's rate, calculate remaining SMS in package
                avg_sms_cost = practice_credit.current_package.credit_per_SMS
                estimated_remaining_SMS = practice_credit.balance // avg_sms_cost

            if practice_credit.current_package.credit_per_VC:

                # using the package's rate, calculate remaining VC in package
                avg_voice_cost = practice_credit.current_package.credit_per_VC
                estimated_remaining_VC = practice_credit.balance // avg_voice_cost

            if not practice_credit.current_package.credit_per_SMS and not practice_credit.current_package.credit_per_VC:

                raise CorruptedPackage(practice_credit.current_package.id, practice_credit.current_package.name)
            
        return JsonResponse({
            "practice_id": practice_id,
            "current_balance": practice_credit.balance,
            "last_purchase": last_purchase_date,
            "estimated_remaining_sms": estimated_remaining_SMS,
            "estimated_remaining_voice": estimated_remaining_VC
        })
    
    except PracticeCredit.DoesNotExist:
        return JsonResponse({"error": "Practice not found"}, status=404)
    
    except CorruptedPackage as e:
        JsonResponse({"error": str(e)}, status=409)

async def transaction_history(request):

    # This path only responds to GET requests
    if request.method != "GET":
        
        return JsonResponse({"error": f"{request.method} method not allowed on this endpoint."}, status=405)
    
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

    if not await queryset.aexists():
        return JsonResponse({"response": f"Practice requested id: {practice_id} hasn't performed any transactions yet"}, status=404)
    
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
    


