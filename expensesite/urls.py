from django.contrib import admin
from django.urls import path
from expenses.views import (
    UserListCreate,
    UserDetail,
    GroupListCreate,
    GroupAddMember,
    ExpenseCreate,
    BalanceList,
    SettlementCreate,
    SimplifyDebts,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Users
    path("api/v1/users", UserListCreate.as_view()),
    path("api/v1/users/<int:pk>", UserDetail.as_view()),

    # Groups
    path("api/v1/groups", GroupListCreate.as_view()),
    path("api/v1/groups/<int:group_id>/members", GroupAddMember.as_view()),

    # Expenses
    path("api/v1/groups/<int:group_id>/expenses", ExpenseCreate.as_view()),

    # Balances
    path("api/v1/groups/<int:group_id>/balances", BalanceList.as_view()),

    # Settlements
    path("api/v1/groups/<int:group_id>/settlements", SettlementCreate.as_view()),

    # Simplify
    path("api/v1/groups/<int:group_id>/simplify", SimplifyDebts.as_view()),
]
