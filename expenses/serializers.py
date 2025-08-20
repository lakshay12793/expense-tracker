from rest_framework import serializers
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from .models import User, ExpenseGroup, GroupMember, Expense, ExpenseShare, Settlement


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseGroup
        fields = ["id", "name", "base_currency"]


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class ExpenseSerializer(serializers.ModelSerializer):
    payer_id = serializers.IntegerField(write_only=True)
    exact_shares = serializers.ListField(
        child=serializers.DecimalField(max_digits=12, decimal_places=2),
        required=False,
    )
    percentages = serializers.ListField(
        child=serializers.DecimalField(max_digits=5, decimal_places=2),
        required=False,
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "payer_id",
            "amount",
            "currency",
            "split_type",
            "description",
            "expense_date",
        ]

    def validate(self, data):
        group = self.context["group"]
        if data["currency"] != group.base_currency:
            raise serializers.ValidationError(
                "Expense currency must match group base currency"
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        group = self.context["group"]
        payer = User.objects.get(pk=validated_data.pop("payer_id"))
        split_type = validated_data["split_type"]

        expense = Expense.objects.create(group=group, payer=payer, **validated_data)

        members = list(
            GroupMember.objects.filter(group=group).order_by("id").values_list("user_id", flat=True)
        )
        amt = expense.amount

        if split_type == "EQUAL":
            share = (amt / Decimal(len(members))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            for uid in members:
                ExpenseShare.objects.create(expense=expense, user_id=uid, share_amount=share)

        elif split_type == "EXACT":
            shares = self.initial_data.get("exact_shares", [])
            if len(shares) != len(members):
                raise serializers.ValidationError("Exact shares must match group size")
            if sum(Decimal(s) for s in shares) != amt:
                raise serializers.ValidationError("Exact shares must sum to total amount")
            for uid, s in zip(members, shares):
                ExpenseShare.objects.create(expense=expense, user_id=uid, share_amount=Decimal(s))

        elif split_type == "PERCENTAGE":
            percs = self.initial_data.get("percentages", [])
            if len(percs) != len(members):
                raise serializers.ValidationError("Percentages must match group size")
            if sum(Decimal(p) for p in percs) != Decimal("100"):
                raise serializers.ValidationError("Percentages must sum to 100")
            for uid, p in zip(members, percs):
                share = (amt * Decimal(p) / Decimal("100")).quantize(Decimal("0.01"))
                ExpenseShare.objects.create(
                    expense=expense, user_id=uid, share_amount=share, share_percent=Decimal(p)
                )

        return expense


class SettlementSerializer(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField(write_only=True)
    to_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Settlement
        fields = ["id", "from_user_id", "to_user_id", "amount", "currency", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, data):
        group = self.context["group"]
        if data["currency"] != group.base_currency:
            raise serializers.ValidationError("Settlement currency mismatch with group")
        if data["from_user_id"] == data["to_user_id"]:
            raise serializers.ValidationError("from_user and to_user cannot be the same")
        return data
