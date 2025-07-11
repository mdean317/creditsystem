class InsufficientCreditsError(Exception):
    """Raised when a user doesn't have enough credits"""
    def __init__(self, amount_required, available):
        message = f"Insufficient credits. Required: {amount_required}, Available: {available}"
        super().__init__(message)


class CreditCardError(Exception):
    """Raised when a user credit card is rejected"""
    def __init__(self, last_four, transaction_id):
        message = f"Transaction using credit card ending with {last_four} failed. For more informarion see transaction number: {transaction_id}"
        super().__init__(message)

    