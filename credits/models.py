from django.db import models
import uuid
from .exceptions import InsufficientCreditsError
from django.core.validators import MinValueValidator

TYPE_PURCHASE = 'PURCHASE'
TYPE_SMS = 'SMS_USAGE'
TYPE_VOICE = 'VOICE_USAGE'

TRANSACTION_TYPES = {
    TYPE_PURCHASE: 'Purchase',
    TYPE_SMS: 'SMS Usage',
    TYPE_VOICE: 'Voice Usage'
}

LOW_CREDITS_THRESHHOLD_PERCENTAGE = 20

class Practice(models.Model):
    """Keeps information on practices using the app"""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.id} - {self.name}"
    
class CreditPackage(models.Model):
    """Represents different credit packages that practices can purchase"""
    name = models.CharField(max_length=100)
    credit_amount = models.PositiveIntegerField()
    price_cents = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    is_package_pay_as_you_go = models.BooleanField(default=True)
    credit_per_SMS = models.FloatField(validators=[MinValueValidator(0.0)], blank=True, null=True)
    credit_per_VC = models.FloatField(validators=[MinValueValidator(0.0)], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.credit_amount} credits"
    
class PracticeCredit(models.Model):
    """Tracks credit balance for a practice"""
    practice = models.OneToOneField(Practice, on_delete=models.CASCADE, primary_key=True)
    balance = models.PositiveIntegerField(default=0)
    current_package = models.ForeignKey(CreditPackage, on_delete=models.SET_NULL, null=True, blank=True)
    pay_as_you_go_SMS_count = models.PositiveIntegerField(default=0, blank=True)
    pay_as_you_go_VC_count = models.PositiveIntegerField(default=0, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    preferred_customer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.practice} - {self.balance} credits"
    
    async def has_sufficient_credits(self, amount):
        """Check if practice has sufficient credits for an operation"""
        return self.balance >= amount
    
    async def deduct_credits(self, amount, transaction_type, reference_id=None):
        """Deduct credits and create a transaction record"""
        if not await self.has_sufficient_credits(amount):
            raise InsufficientCreditsError(amount, self.balance)
        
        async with transaction.atomic():
            """Run atomic db transaction - balance update and transaction log"""
            self.balance -= amount
            await self.asave()
            
            # Create transaction record
            transaction = CreditTransaction(
                practice=self.practice,
                amount=-amount,
                transaction_type=transaction_type,
                reference_id=reference_id or uuid.uuid4()
            )
            await transaction.asave()
            return transaction
        
    async def last_purchase_date(self):
        """Get last purchase date for practice"""
       
        last_purchase_date = await (
        CreditTransaction.objects
        .filter(practice_id=self.practice_id, transaction_type=TYPE_PURCHASE)
        .order_by('-created_at')
        .values_list("created_at", flat=True)
        .afirst()
    )
        return(last_purchase_date)
    
    async def are_credits_low(self):
        """Get data on last purchased package"""
        credits_purchased = await CreditTransaction.objects.filter(practice_id=self.practice.id, transaction_type=TYPE_PURCHASE).order_by('-created_at').values_list("package__credit_amount", flat=True).afirst()
        if (self.balance / credits_purchased * 100 < LOW_CREDITS_THRESHHOLD_PERCENTAGE):
            return(True)

class CreditTransaction(models.Model):
    """Records package purchases and credit usage"""
    
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE)
    amount = models.IntegerField()  # Positive for purchases, negative for usage
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    package = models.ForeignKey(CreditPackage, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    reference_id = models.UUIDField(default=uuid.uuid4)  # For tracking specific usage events
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional info
    class Meta:
        indexes = [
            models.Index(fields=["practice", "transaction_type", "created_at"]),
        ]
    def __str__(self):
        return f"{self.practice.name} - {self.transaction_type} - {self.amount}"
    