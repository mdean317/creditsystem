from .models import PracticeCredit, TYPE_SMS, TYPE_VOICE
from .exceptions import CorruptedPackage
from django.db.models import F
import math

"""This file is for additional functions and logic that is needed, but felt more readable to separate from models and views"""
"""buySMS and buyVC arem't called anywhere in the app"""
"""TODO: create RESTful endpoint to purchase SMS and VC, to call these functions """

SEGMENT_LENGTH = 153

SMS_PAY_AS_YOU_GO_THRESHOLDS = [
    {"threshold": 500, "rate": 85},
    {"threshold": 1000, "rate": 83},
    {"threshold": 2000, "rate": 81},
    {"threshold": 3000, "rate": 79},
    {"threshold": 5000, "rate": 77},
    {"threshold": -1, "rate": 74},
]

VC_PAY_AS_YOU_GO_THRESHOLDS = [
    {"threshold": 500, "rate": 160},
    {"threshold": 1000, "rate": 158},
    {"threshold": 2000, "rate": 156},
    {"threshold": 5000, "rate": 154},
    {"threshold": 10000, "rate": 152},
    {"threshold": -1, "rate": 149},
]

MORNING = 'MORNING'
MIDDAY = 'MIDDAY'
AFTERNOON = 'AFTERNOON'
EVENING = 'EVENING'

TIMES_OF_DAY = {
    MORNING: 'Morning',
    MIDDAY: 'Midday',
    AFTERNOON: 'Afternoon',
    EVENING: 'Evening',
}

def calc_SMS_pay_as_you_go_remaining(curr_balance, SMS_transactions):
    '''calcultes how many SMS are remaining in pay as you go based on credit balance'''     
    
    # Initaite variables
    SMS_since_last_purchase = 0
    SMS_remaining = 0
    i = 0

    for transaction in SMS_transactions:
        '''runs through all SMS transactions since package was bought'''
        '''TODO: devise a business solution and implement for when user buys more credits on pay-as-you-go: differentiate between 'starting package' and adding credits'''

        # Get number of SMS sent since package was bought
        SMS_since_last_purchase += transaction.amount

        # If a new pay-as-you-go threshold was reached, adjust counter
        if SMS_since_last_purchase > SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]:
            i += 1

            # if we reached the final threshhold, calculate remaining SMS based on rate, and exit loop
            if i == len(SMS_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                break
    
    # Count remaining SMS until credits run out or until we are at the last threshhold 
    while  i < len(SMS_PAY_AS_YOU_GO_THRESHOLDS) - 1:
        SMS_for_next_threshold = SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"] - SMS_since_last_purchase
        credits_for_next_threshold = SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"] * SMS_for_next_threshold

        if curr_balance <= credits_for_next_threshold:
            # If remaining credits aren't enough to cross to next threshold, we can break
            break
        else:
            # otherwise add SMS in threshold to our SMS sum, and deduct cost from balance
            SMS_remaining += SMS_for_next_threshold
            curr_balance -= SMS_for_next_threshold * SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
            i+=1

    # Add SMS based on last reached threshhold rate and remaining balance
    SMS_remaining += curr_balance / SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]

    return (math.floor(SMS_remaining))

def calc_VC_pay_as_you_go_remaining(curr_balance, VC_transactions):
    '''calcultes how many VC minutes are remaining in pay as you go based on credit balance'''     
    
    # Initaite variables
    VC_since_last_purchase = 0
    VC_remaining = 0
    i = 0

    for transaction in VC_transactions:
        '''runs through all VC transactions since package was bought'''
        '''TODO: devise a business solution and implement for when user buys more credits on pay-as-you-go: differentiate between 'starting package' and adding credits'''

        # Get number os SMS sent since package was bough
        VC_since_last_purchase += transaction.amount

        # If a new pay as you go threshold was reached, adjust counter
        if VC_since_last_purchase > VC_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]:
            i += 1

            # if we reached the final threshhold, calculate remaining VC mins based on rate, and exit loop
            if i == len(VC_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                break
    
    # Count remaining VC mins until credits run out or until we are at the last threshhold 
    while  i < len(VC_PAY_AS_YOU_GO_THRESHOLDS) - 1:
        VC_for_next_threshold = VC_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"] - VC_since_last_purchase
        credits_for_next_threshold = VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"] * VC_for_next_threshold

        if curr_balance <= credits_for_next_threshold:
            # If remaining credits aren't enough to cross to next threshold, we can break
            break
        else:
            # otherwise add VC mins in threshold to our VC sum, and deduct cost from balance
            VC_remaining += VC_for_next_threshold
            curr_balance -= VC_for_next_threshold * VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
            i+=1

    # Add VC based on last reached threshhold rate and remaining balance
    VC_remaining += curr_balance / VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]

    return (math.floor(VC_remaining))

async def buySMS(practice_id, number_of_recipients, message):
    '''buy SMS messages for practice'''

    # Get the practice and package info
    practice_credit = await PracticeCredit.objects.select_related('current_package').aget(practice_id=practice_id)
    is_pay_as_you_go = practice_credit.current_package.is_package_pay_as_you_go

    # Calculate # of texts to send 
    segments = len(message) // SEGMENT_LENGTH
    if (len(message) % SEGMENT_LENGTH > 0):
            segments += 1
    num_of_SMS_to_send = segments * number_of_recipients

    def calc_cost_of_SMS_campaign_for_pay_as_you_go(SMS_count, num_of_SMS_to_send):
        '''calculate cost of SMS campaign in a pay-as-you-go package'''

        # initiate variables
        SMS_already_sent_in_package = SMS_count
        i = 0
        threshhold_sum = SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"] 
        credits_needed = 0
        
        while SMS_already_sent_in_package < threshhold_sum:
            '''iterate until we get to the threshold we are currently in'''
            i += 1
            if i == len(SMS_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                credits_needed = num_of_SMS_to_send * SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
                return(credits_needed)
            threshhold_sum += SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]
            
        SMS_remaining_in_threshhold = threshhold_sum - SMS_already_sent_in_package
        while num_of_SMS_to_send >= SMS_remaining_in_threshhold: 
            '''iterate until the cost for all SMS requested is calculate, or you reach the last threshold '''
            credits_needed += SMS_remaining_in_threshhold * SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
            num_of_SMS_to_send -= SMS_remaining_in_threshhold
            i += 1
            # if last threshhold has been reached, calc remaining SMS to send and return val
            if i == len(SMS_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                credits_needed += num_of_SMS_to_send * SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
                return(credits_needed)
        
            # otherwise get next threshold
            SMS_remaining_in_threshhold = SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]

        # add cost of remaining SMS based on current threshold rate
        credits_needed += num_of_SMS_to_send * SMS_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
        return(credits_needed)

    # Calculate cost of requested SMS campaign 
    if is_pay_as_you_go:
        '''if program is pay_as_you_go'''

        # call function to calculate pay as you
        credits_needed = calc_cost_of_SMS_campaign_for_pay_as_you_go(practice_credit.pay_as_you_go_SMS_count, num_of_SMS_to_send)
        
    else:
        '''if program is prepaid'''

        # check package has relevant rate
        if not practice_credit.current_package.credit_per_SMS:
            raise CorruptedPackage(practice_credit.current_package.id, practice_credit.current_package.name)
            
        # calc credits needed based on package rate
        credits_needed = num_of_SMS_to_send * practice_credit.current_package.credit_per_SMS

    # try to execute package - function will check if practice has enough credits. If yes, it will produce a transaction, if not it will raise an error. 
    transaction = await practice_credit.deduct_credits(credits_needed, TYPE_SMS)

    if transaction:
        '''if a transaction took place, update SMS count in practice credit'''
        practice_credit.pay_as_you_go_SMS_count = F('pay_as_you_go_SMS_count') + num_of_SMS_to_send
        practice_credit.save(update_fields=["pay_as_you_go_SMS_count"])
    
    return(transaction)
            
async def buyVC(practice_id, number_of_recipients, call_minutes,time_of_day):
    '''buy VC for practice'''

    # Get the practice and package info
    practice_credit = await PracticeCredit.objects.select_related('current_package').aget(practice_id=practice_id)
    is_pay_as_you_go = practice_credit.current_package.is_package_pay_as_you_go
    
    '''TODO: Adjust pricing based on `time_of_day` (MORNING, MIDDAY, etc.)'''
    num_of_minutes_to_use = call_minutes * number_of_recipients

    def calc_cost_of_VC_campaign_for_pay_as_you_go(VC_mins_count, num_of_minutes_to_use):
        '''calculate cost of VC campaign in a pay-as-you-go package'''

        # initiate variables
        VC_mins_already_used_in_package = VC_mins_count
        i = 0
        threshhold_sum = VC_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"] 
        credits_needed = 0
        
        while VC_mins_already_used_in_package < threshhold_sum:
            '''iterate until we get to the threshold we are currently in'''
            i += 1
            if i == len(VC_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                credits_needed = num_of_minutes_to_use * VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
                return(credits_needed)
            threshhold_sum += VC_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]
            
        VC_mins_remaining_in_threshhold = threshhold_sum - VC_mins_already_used_in_package
        while num_of_minutes_to_use >= VC_mins_remaining_in_threshhold: 
            '''iterate until the cost for all VC mins requested is calculate, or you reach the last threshold '''
            credits_needed += VC_mins_remaining_in_threshhold * VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
            num_of_minutes_to_use -= VC_mins_remaining_in_threshhold
            i += 1
            # if last threshhold has been reached, calc remaining SMS to send and return val
            if i == len(VC_PAY_AS_YOU_GO_THRESHOLDS) - 1:
                credits_needed += num_of_minutes_to_use * VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
                return(credits_needed)
            # otherwise get next threshold
            VC_mins_remaining_in_threshhold = VC_PAY_AS_YOU_GO_THRESHOLDS[i]["threshold"]
        
        # add cost of remaining minutes based on current threshold rate
        credits_needed += num_of_minutes_to_use * VC_PAY_AS_YOU_GO_THRESHOLDS[i]["rate"]
        return(credits_needed)

    # Calculate cost of requested VC campaign 
    if is_pay_as_you_go:
        '''if program is pay_as_you_go'''

        # call function to calculate pay as you
        credits_needed = calc_cost_of_VC_campaign_for_pay_as_you_go(practice_credit.pay_as_you_go_VC_count, num_of_minutes_to_use)
        
    else:
        '''if program is prepaid'''

        # check package has relevant rate
        if not practice_credit.current_package.credit_per_VC:
            raise CorruptedPackage(f"Package {practice_credit.current_package.id} - {practice_credit.current_package.name} has no rates for the action you are trying to do")
            
        # calc credits needed based on package rate
        credits_needed = num_of_minutes_to_use * practice_credit.current_package.credit_per_VC

    # try to execute package - function will check if practice has enough credits. If yes, it will produce a transaction, if not it will raise an error. 
    transaction = await practice_credit.deduct_credits(credits_needed, TYPE_VOICE)

    if transaction:
        '''if a transaction took place, update VC min count in practice credit'''
        practice_credit.pay_as_you_go_VC_count = F('pay_as_you_go_VC_count') + num_of_minutes_to_use
        practice_credit.save(update_fields=["pay_as_you_go_VC_count"])
    
    return(transaction)
    
        