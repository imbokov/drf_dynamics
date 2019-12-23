from rest_framework.viewsets import GenericViewSet

from drf_dynamics.helpers import dynamic_queryset
from drf_dynamics.mixins import DynamicQuerySetMixin
from drf_dynamics.specs import DynamicPrefetch
from .models import Invite, Party


@dynamic_queryset(
    prefetches=(
        "invites.answer",
        "invites.answer.details",
        {"invites": DynamicPrefetch("invites", Invite.objects.for_user)},
    ),
    annotations=(
        "invites_count",
        "invites.has_answer",
        "invites.answer.all_details_reviewed",
    ),
    selects=(
        "host",
        "invites.sender",
        "invites.recipient",
        "invites.answer.details.reviewer",
    ),
)
class PartyViewSet(DynamicQuerySetMixin, GenericViewSet):
    queryset = Party.objects.all()
