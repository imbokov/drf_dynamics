from django.db import models

from .helpers import MockRequest
from .testcases import TestCase
from ..models import Answer, Details, Invite, Party, Person
from ..views import PartyViewSet


class DynamicQuerySetMixinTestCase(TestCase):
    def setUp(self):
        self.viewset_class = PartyViewSet
        self.user = Person.objects.create()

    def test_requested_fields_cached(self):
        viewset = self.viewset_class(
            request=MockRequest(query_params={"fields": "foo,bar"})
        )
        first_fields = viewset.requested_fields
        viewset.request.query_params["fields"] = "baz"
        self.assertIs(first_fields, viewset.requested_fields)

    def test_dynamic_fields_actions(self):
        query_params = {"fields": "host.id,invites.answer.id"}
        viewset = self.viewset_class(
            request=MockRequest(query_params=query_params), action="destroy"
        )
        self.assertQuerysetsEqual(
            Party.objects.all(), viewset.get_queryset(),
        )

    def test_get_queryset(self):
        """Various scenarios"""
        for query_params, queryset in (
            (
                {"fields": "host.id,invites.answer.id"},
                Party.objects.prefetch_related(
                    models.Prefetch(
                        "invites",
                        Invite.objects.for_user(
                            MockRequest(user=self.user)
                        ).prefetch_related(
                            models.Prefetch("answer", Answer.objects.all())
                        ),
                    )
                ),
            ),
            (
                {"fields": "host.id,host.username,invites.answer.id"},
                Party.objects.prefetch_related(
                    models.Prefetch(
                        "invites",
                        Invite.objects.for_user(
                            MockRequest(user=self.user)
                        ).prefetch_related(
                            models.Prefetch("answer", Answer.objects.all())
                        ),
                    )
                ).select_related("host"),
            ),
            (
                {"fields": "host.id,host.username,invites_count"},
                Party.objects.with_invites_count(None).select_related("host"),
            ),
            (
                {
                    "fields": "invites.answer.all_details_reviewed,"
                    "invites.answer.details.reviewer.id"
                },
                Party.objects.prefetch_related(
                    models.Prefetch(
                        "invites",
                        Invite.objects.for_user(
                            MockRequest(user=self.user)
                        ).prefetch_related(
                            models.Prefetch(
                                "answer",
                                Answer.objects.with_all_details_reviewed(
                                    None
                                ).prefetch_related(
                                    models.Prefetch("details", Details.objects.all())
                                ),
                            ),
                        ),
                    )
                ),
            ),
        ):
            viewset = self.viewset_class(
                request=MockRequest(query_params=query_params, user=self.user),
                action="list",
            )
            self.assertQuerysetsEqual(
                queryset, viewset.get_queryset(),
            )

    def test_get_queryset_no_fields(self):
        viewset = self.viewset_class(
            request=MockRequest(query_params={}, user=self.user), action="list",
        )
        self.assertQuerysetsEqual(
            Party.objects.prefetch_related(
                models.Prefetch(
                    "invites",
                    Invite.objects.for_user(MockRequest(user=self.user))
                    .prefetch_related(
                        models.Prefetch(
                            "answer",
                            Answer.objects.with_all_details_reviewed(
                                None
                            ).prefetch_related(
                                models.Prefetch(
                                    "details",
                                    Details.objects.select_related("reviewer"),
                                )
                            ),
                        ),
                    )
                    .with_has_answer(None)
                    .select_related("recipient", "sender"),
                )
            )
            .with_invites_count(None)
            .select_related("host"),
            viewset.get_queryset(),
        )
