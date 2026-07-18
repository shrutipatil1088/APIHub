import uuid

from django.db import models

from apps.accounts.models import User
from apps.core.models.base import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Represents a subscription plan offered to developers.
    """

    class BillingCycle(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        YEARLY = "YEARLY", "Yearly"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )

    request_limit = models.PositiveIntegerField(
        help_text="Maximum API requests allowed during one billing cycle."
    )

    class Meta:
        db_table = "subscription_plans"
        ordering = ["price"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_this_free = (
            self.price == 0 or
            "free" in self.name.strip().lower()
        )
        if self.is_active and is_this_free:
            from django.db import transaction
            from django.db.models import Q
            with transaction.atomic():
                qs = SubscriptionPlan.objects.filter(
                    Q(price=0) | Q(name__icontains="free"),
                    is_active=True,
                    is_deleted=False,
                )
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                qs.update(is_active=False)
        super().save(*args, **kwargs)



class UserSubscription(BaseModel):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"
        PENDING = "PENDING", "Pending"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    auto_renew = models.BooleanField(default=True)

    class Meta:
        db_table = "user_subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"