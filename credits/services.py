
from .models import CreditPackage,  Practice, CreditTransaction


def sendSMS(practice_id, number_of_recipients, recipients, message, date):


    '''Get the practice info'''
    practice = Practice.objects.get(id=practice_id)

    '''Make adjustments to credit exchange value based on package'''
    amount = 0

    '''Check practice has enough credits'''
    if (practice.has_sufficient_credits(amount)):
         
        transaction_id = practice.deduct_credits(amount, 'SMS_USAGE')

    threshhold = 100 #TBD
    if (practice.credit_amount < threshhold): 
        #Do something
        threshhold = 0

def buyVCs(practice_id, number_of_recipients, recipients, duration, call, date):

    '''Get the practice info'''
    practice = Practice.objects.get(id=practice_id)

    '''Make adjustments to credit exchange value based on package'''
    amount = 0

    '''Check practice has enough credits'''
    if (practice.has_sufficient_credits(amount)):
         
        transaction_id = practice.deduct_credits(amount, 'VOICE_USAGE')

    threshhold = 100 #TBD
    if (practice.credit_amount < threshhold): 
        #Do something
         threshhold = 0

def calcCreditsForSMS():
    print('tbd')


def calcCreditsForVC():
    print('tbd')

