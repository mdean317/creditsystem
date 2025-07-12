from collections import namedtuple
from credits.services import SEGMENT_LENGTH, buySMS
import random
import pytest

'''Test Cases for calc_SMS_pay_as_you_go_remaining
    no practice id
    practice id can't be found
    negative number of number_of_recipients
    empty message
    pay as you go package
    regular package
    message that is more than one segment
    pay_as_you_go at first threshhold
    pay_as_you_go at middle threshhold
    pay_as_you_go at last threshhold
    regular package has no rate for SMS
    credits needed more than practice has
    credits needed less than practice has
    credits needed equal than practice has
'''