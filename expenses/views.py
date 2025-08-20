from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import User, ExpenseGroup, GroupMember, Settlement
from .serializers import (
    UserSerializer,
    GroupSerializer,
    AddMemberSerializer,
    ExpenseSerializer,
    SettlementSerializer,
)
from .services import compute_balances, amount_owed_from_to, suggest_min_cash_flow


# USERS
class UserListCreate(APIView):
    def post(self, request):
        s = UserSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)


class UserDetail(APIView):
    def get(self, request, pk):
        u = get_object_or_404(User, pk=pk)
        return Response(UserSerializer(u).data)


# GROUPS
class GroupListCreate(APIView):
    def post(self, request):
        s = GroupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        g = s.save()
        return Response(GroupSerializer(g).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        groups = ExpenseGroup.objects.all()
        return Response(GroupSerializer(groups, many=True).data)


class GroupAddMember(APIView):
    def post(self, request, group_id):
        group = get_object_or_404(ExpenseGroup, pk=group_id)
        s = AddMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=s.validated_data["user_id"])
        GroupMember.objects.get_or_create(group=group, user=user)
        return Response({"message": "Member added"}, status=status.HTTP_201_CREATED)


# EXPENSES
class ExpenseCreate(APIView):
    def post(self, request, group_id):
        group = get_object_or_404(ExpenseGroup, pk=group_id)
        s = ExpenseSerializer(data=request.data, context={"group": group})
        s.is_valid(raise_exception=True)
        expense = s.save()
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


# BALANCES
class BalanceList(APIView):
    def get(self, request, group_id):
        net, pair = compute_balances(group_id)
        result = []
        for uid, bal in net.items():
            result.append(
                {
                    "user_id": uid,
                    "net_balance": str(bal),
                    "pairwise_balances": {str(k): str(v) for k, v in pair.get(uid, {}).items()},
                }
            )
        return Response(result)


# SETTLEMENTS
class SettlementCreate(APIView):
    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(ExpenseGroup, pk=group_id)
        s = SettlementSerializer(data=request.data, context={"group": group})
        s.is_valid(raise_exception=True)

        from_user_id = s.validated_data["from_user_id"]
        to_user_id = s.validated_data["to_user_id"]
        amount = s.validated_data["amount"]

        net, pair = compute_balances(group.id)
        owed = amount_owed_from_to(pair, from_user_id, to_user_id)
        if amount > owed:
            return Response(
                {"detail": f"Invalid settlement: trying to settle {amount}, but owed only {owed}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settlement = Settlement.objects.create(
            group=group,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=amount,
            currency=s.validated_data["currency"],
            status="COMPLETED",
        )
        return Response(SettlementSerializer(settlement).data, status=status.HTTP_201_CREATED)


# SIMPLIFY
class SimplifyDebts(APIView):
    def post(self, request, group_id):
        net, _ = compute_balances(group_id)
        suggestions = suggest_min_cash_flow(net)
        return Response(suggestions)
