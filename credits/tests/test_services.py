from asgiref.testing import async_to_sync
from django.test import TestCase
'''
from your_app.services import deduct_credits
class DeductCreditsTest(TestCase):

    def test_insufficient_balance(self):
        practice = Practice.objects.create(balance=5)
        with self.assertRaises(InsufficientCreditsError):
        async_to_sync(deduct_credits)(practice, 10)'''