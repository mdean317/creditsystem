from rest_framework.test import APITestCase, APIClient
'''
class BalanceViewTest(APITestCase):
        def setUp(self):
            self.client = APIClient()
            self.practice = Practice.objects.create(...)
        def test_balance_fetch_success(self):
            response = self.client.get(f"/api/credits/balance/?
            practice_id={self.practice.id}")
            self.assertEqual(response.status_code, 200)'''