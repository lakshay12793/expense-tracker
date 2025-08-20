from .models import Expense, GroupMember, Settlement
from decimal import Decimal


def compute_balances(group_id):
    members = list(GroupMember.objects.filter(group_id=group_id).values_list("user_id", flat=True))
    net = {uid: Decimal("0.00") for uid in members}
    pair = {uid: {} for uid in members}

    # Expenses
    expenses = Expense.objects.filter(group_id=group_id).select_related("payer").prefetch_related("shares")
    for e in expenses:
        for s in e.shares.all():
            uid = s.user_id
            net[uid] -= s.share_amount
            pair[uid][e.payer_id] = pair[uid].get(e.payer_id, Decimal("0.00")) + s.share_amount
        net[e.payer_id] += e.amount

    # Settlements
    for s in Settlement.objects.filter(group_id=group_id):
        net[s.from_user_id] -= s.amount
        net[s.to_user_id] += s.amount
        pair[s.from_user_id][s.to_user_id] = pair[s.from_user_id].get(s.to_user_id, Decimal("0.00")) + s.amount

    return net, pair


def amount_owed_from_to(pair, from_user_id, to_user_id):
    return Decimal(pair.get(from_user_id, {}).get(to_user_id, "0.00"))


def suggest_min_cash_flow(net):
    debtors = [(u, -amt) for u, amt in net.items() if amt < 0]
    creditors = [(u, amt) for u, amt in net.items() if amt > 0]

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    i = j = 0
    suggestions = []

    while i < len(debtors) and j < len(creditors):
        du, da = debtors[i]
        cu, ca = creditors[j]
        paid = min(da, ca)
        suggestions.append({"from_user_id": du, "to_user_id": cu, "amount": paid})
        da -= paid
        ca -= paid
        if da == 0:
            i += 1
        else:
            debtors[i] = (du, da)
        if ca == 0:
            j += 1
        else:
            creditors[j] = (cu, ca)
    return suggestions
