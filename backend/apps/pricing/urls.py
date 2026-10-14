from django.urls import path
from apps.pricing.views import (
    PriceListListCreateView,
    PriceListDetailView,
    PriceListItemListCreateView,
    PriceListItemDetailView,
    PriceListJobRuleListCreateView,
    PriceListJobRuleDetailView,
    PricingResolveView,
    PricingAuditListView,
    PricingSeedDefaultsView
)

app_name = "pricing"

urlpatterns = [
    path("lists/", PriceListListCreateView.as_view(), name="price_list_list_create"),
    path("lists/<int:pk>/", PriceListDetailView.as_view(), name="price_list_detail"),
    path("lists/<int:list_id>/items/", PriceListItemListCreateView.as_view(), name="price_list_items"),
    path("items/<int:pk>/", PriceListItemDetailView.as_view(), name="price_list_item_detail"),
    path("lists/<int:list_id>/job-rules/", PriceListJobRuleListCreateView.as_view(), name="price_list_job_rules"),
    path("job-rules/<int:pk>/", PriceListJobRuleDetailView.as_view(), name="price_list_job_rule_detail"),
    path("resolve/", PricingResolveView.as_view(), name="pricing_resolve"),
    path("audit/", PricingAuditListView.as_view(), name="pricing_audit"),
    path("seed-defaults/", PricingSeedDefaultsView.as_view(), name="pricing_seed_defaults"),
]
