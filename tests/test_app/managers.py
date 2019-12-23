from django.db import models


class PartyQuerySet(models.QuerySet):
    def with_invites_count(self, request):
        from .models import Invite

        return self.annotate(
            invites_count=models.Subquery(
                Invite.objects.filter(party=models.OuterRef("pk"))
                .order_by()
                .values("party")
                .annotate(count=models.Count("pk"))
                .values("count")
            )
        )


class PartyManager(models.Manager.from_queryset(PartyQuerySet)):
    pass


class InviteQuerySet(models.QuerySet):
    def for_user(self, request):
        return self.filter(
            models.Q(recipient=request.user)
            | models.Q(sender=request.user)
            | models.Q(party__host=request.user)
        )

    def with_has_answer(self, request):
        return self.annotate(answer__isnull=False)


class InviteManager(models.Manager.from_queryset(InviteQuerySet)):
    pass


class AnswerQuerySet(models.QuerySet):
    def with_all_details_reviewed(self, request):
        from .models import Details

        return self.annotate(
            all_details_reviewed=~models.Exists(
                Details.objects.filter(answer=models.OuterRef("pk"), reviewed=False)
            )
        )


class AnswerManager(models.Manager.from_queryset(AnswerQuerySet)):
    pass
