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

class CorruptedPackage(Exception):
    """Raised when a package has no rates"""
    def __init__(self, package_id, package_name):
        message = f"Package {package_id} - {package_name}  has no rates for the action you are trying to do"
        super().__init__(message)

class PracticeDoesNotExist(Exception):
    """Raised when a practice id doesn't exist in db"""
    def __init__(self, practice_id):
        message = f"Practice for practice_id {practice_id} does not exist"
        super().__init__(message)

class PracticeCreditDoesNotExist(Exception):
    """Raised when a practiceCredit id doesn't exist in db"""
    def __init__(self, practice_id):
        message = f"PracticeCredit for practice_id {practice_id} does not exist"
        super().__init__(message)
