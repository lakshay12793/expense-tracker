from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone

currency_validator = RegexValidator(r"^[A-Z]{3}$", "Currency must be a 3-letter code")

class User(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ExpenseGroup(models.Model):
    name = models.CharField(max_length=160)
    base_currency = models.CharField(max_length=3, validators=[currency_validator])
    created_at = models.DateTimeField(auto_now_add=True)

class GroupMember(models.Model):
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name="members")
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    role  = models.CharField(max_length=30, default="MEMBER")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

class Expense(models.Model):
    SPLIT_CHOICES = [("EQUAL","EQUAL"),("EXACT","EXACT"),("PERCENTAGE","PERCENTAGE")]
    group      = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name="expenses")
    payer      = models.ForeignKey(User, on_delete=models.PROTECT, related_name="paid_expenses")
    amount     = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency   = models.CharField(max_length=3, validators=[currency_validator])
    split_type = models.CharField(max_length=20, choices=SPLIT_CHOICES)
    description = models.TextField(blank=True, null=True)
    expense_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

class ExpenseShare(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="shares")
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shares")
    share_amount  = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    share_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ("expense", "user")

class Settlement(models.Model):
    group   = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name="settlements")
    from_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="settlements_made")
    to_user   = models.ForeignKey(User, on_delete=models.PROTECT, related_name="settlements_received")
    amount    = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency  = models.CharField(max_length=3, validators=[currency_validator])
    status    = models.CharField(max_length=20, default="COMPLETED")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.from_user_id == self.to_user_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("from_user and to_user cannot be the same")

class AuditEvent(models.Model):
    EVENT_CHOICES = [("EXPENSE","EXPENSE"),("SETTLEMENT","SETTLEMENT")]
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
