from typing import TypeVar, Generic, Type, Optional
from django.db.models import QuerySet, Model

T = TypeVar('T', bound=Model)

class BaseRepository(Generic[T]):
    model: Type[T] = None

    @classmethod
    def get_queryset(cls) -> QuerySet[T]:
        qs = cls.model.objects.all()
        if hasattr(cls.model, 'is_deleted'):
            qs = qs.filter(is_deleted=False)
        return qs

    @classmethod
    def get_by_id(cls, entity_id: int) -> Optional[T]:
        return cls.get_queryset().filter(id=entity_id).first()

    @classmethod
    def list_all(cls) -> QuerySet[T]:
        return cls.get_queryset().order_by('-id')

    @classmethod
    def create(cls, **data) -> T:
        return cls.model.objects.create(**data)

    @classmethod
    def update(cls, instance: T, **data) -> T:
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @classmethod
    def soft_delete(cls, instance: T, user=None) -> None:
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete(user=user)
        else:
            instance.delete()


class CompanyScopedRepository(BaseRepository[T]):
    @classmethod
    def get_for_company(cls, company_id: int) -> QuerySet[T]:
        return cls.get_queryset().filter(company_id=company_id)

    @classmethod
    def get_by_id_and_company(cls, entity_id: int, company_id: int) -> Optional[T]:
        return cls.get_for_company(company_id).filter(id=entity_id).first()
