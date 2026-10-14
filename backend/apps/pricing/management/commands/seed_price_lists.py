from django.core.management.base import BaseCommand
from apps.authentication.models import Company, User
from apps.pricing.services import PriceListService
from core.constants import UserRoles


class Command(BaseCommand):
    help = "Seeds default realistic Yarn Purchase, Sales, and Party Contract price lists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--company_id",
            type=int,
            default=None,
            help="Company ID to seed price lists for (default: all active companies)"
        )

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        if company_id:
            companies = Company.objects.filter(id=company_id)
        else:
            companies = Company.objects.filter(is_active=True, is_deleted=False)

        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found to seed price lists."))
            return

        superadmin = User.objects.filter(role=UserRoles.SUPER_ADMIN).first()
        user_id = superadmin.id if superadmin else None

        for comp in companies:
            self.stdout.write(f"Seeding price lists for Company #{comp.id} ({comp.name})...")
            lists = PriceListService.seed_default_price_lists(company_id=comp.id, user_id=user_id)
            self.stdout.write(self.style.SUCCESS(f"  Successfully seeded/verified {len(lists)} price lists for {comp.name}."))

        self.stdout.write(self.style.SUCCESS("All price lists seeded successfully!"))
