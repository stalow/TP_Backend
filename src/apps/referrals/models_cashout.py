from django.db import models
from apps.accounts.models import User
from apps.organizations.models import Organization


class CashOutRequest(models.Model):
    """
    Request from a referrer to cash out their rewards.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        PAYPAL = "paypal", "PayPal"
        STRIPE = "stripe", "Stripe"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cash_out_requests"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    payment_details = models.JSONField(default=dict)  # Bank account, PayPal email, etc.
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_out_requests"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Cash out €{self.amount} for {self.user.email} - {self.status}"
