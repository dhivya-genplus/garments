from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to resolve and attach active company and active financial year to request.
    """
    def process_request(self, request):
        request.company = None
        request.financial_year = None
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            # 1. Company Resolution
            header_company_id = request.headers.get('X-Company-ID')
            if getattr(user, 'is_superadmin', False) and header_company_id:
                try:
                    from apps.authentication.models import Company
                    request.company = Company.objects.filter(id=header_company_id, is_deleted=False).first()
                except Exception:
                    request.company = None
            else:
                request.company = getattr(user, 'company', None)

            # 2. Financial Year Resolution
            header_fy_id = request.headers.get('X-Financial-Year-ID')
            if header_fy_id:
                try:
                    from apps.authentication.models import FinancialYear
                    fy_qs = FinancialYear.objects.filter(id=header_fy_id, is_deleted=False)
                    if request.company:
                        fy_qs = fy_qs.filter(company=request.company)
                    request.financial_year = fy_qs.first()
                except Exception:
                    request.financial_year = None

            if not request.financial_year:
                request.financial_year = getattr(user, 'active_financial_year', None)
                if not request.financial_year and request.company:
                    request.financial_year = getattr(request.company, 'current_financial_year', None)
