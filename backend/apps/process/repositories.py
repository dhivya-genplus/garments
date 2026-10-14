from typing import Optional
from django.db.models import QuerySet
from apps.process.models import JobWorkMaster, JobWorkPartyConfiguration


class JobWorkRepository:
    """
    Data Access Layer for JobWorkMaster (tm_job_work).
    Encapsulates all ORM queries and multi-tenant scoping.
    """

    @staticmethod
    def get_by_id(job_work_id: int, company_id: int) -> Optional[JobWorkMaster]:
        return JobWorkMaster.objects.filter(
            id=job_work_id,
            company_id=company_id,
            record_status="A"
        ).first()

    @staticmethod
    def get_by_code(code: str, company_id: int) -> Optional[JobWorkMaster]:
        return JobWorkMaster.objects.filter(
            job_work_code__iexact=code,
            company_id=company_id,
            record_status="A"
        ).first()

    @staticmethod
    def list_by_company(
        company_id: int,
        category: Optional[str] = None,
        material_type: Optional[str] = None,
        process_stage_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> QuerySet[JobWorkMaster]:
        qs = JobWorkMaster.objects.filter(
            company_id=company_id,
            record_status="A"
        )
        if category:
            qs = qs.filter(job_work_category=category.upper())
        if material_type:
            qs = qs.filter(material_type=material_type.upper())
        if process_stage_id:
            qs = qs.filter(process_stage_id=process_stage_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs.order_by("job_work_code")

    @staticmethod
    def create(data: dict) -> JobWorkMaster:
        return JobWorkMaster.objects.create(**data)

    @staticmethod
    def update(instance: JobWorkMaster, data: dict) -> JobWorkMaster:
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class JobWorkPartyConfigRepository:
    """
    Data Access Layer for JobWorkPartyConfiguration (tm_job_work_party_config).
    """

    @staticmethod
    def get_by_id(config_id: int, company_id: int) -> Optional[JobWorkPartyConfiguration]:
        return JobWorkPartyConfiguration.objects.filter(
            id=config_id,
            company_id=company_id,
            record_status="A"
        ).first()

    @staticmethod
    def get_active_config(
        job_work_id: int,
        party_id: int,
        company_id: int,
        target_date=None
    ) -> Optional[JobWorkPartyConfiguration]:
        qs = JobWorkPartyConfiguration.objects.filter(
            company_id=company_id,
            job_work_id=job_work_id,
            party_id=party_id,
            is_active=True,
            record_status="A"
        )
        if target_date:
            qs = qs.filter(effective_from__lte=target_date, effective_to__gte=target_date)
        return qs.order_by("-effective_from").first()

    @staticmethod
    def list_by_company(
        company_id: int,
        job_work_id: Optional[int] = None,
        party_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> QuerySet[JobWorkPartyConfiguration]:
        qs = JobWorkPartyConfiguration.objects.filter(
            company_id=company_id,
            record_status="A"
        )
        if job_work_id:
            qs = qs.filter(job_work_id=job_work_id)
        if party_id:
            qs = qs.filter(party_id=party_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs.order_by("-effective_from", "-id")

    @staticmethod
    def create(data: dict) -> JobWorkPartyConfiguration:
        return JobWorkPartyConfiguration.objects.create(**data)

    @staticmethod
    def update(instance: JobWorkPartyConfiguration, data: dict) -> JobWorkPartyConfiguration:
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
