from django.db import models

from .helpers import MockRequest
from .testcases import TestCase
from ..models import Answer, Details, Invite, Party, Person
from ..serializers import PartySerializer
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
        self.assertQuerysetsEqual(Party.objects.all(), viewset.get_queryset())

    def test_get_queryset(self):
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
                {"fields": "host.id,host.name,invites.answer.id"},
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
                {"fields": "host.id,host.name,invites_count"},
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
            self.assertQuerysetsEqual(queryset, viewset.get_queryset())

    def test_get_queryset_no_fields(self):
        viewset = self.viewset_class(
            request=MockRequest(query_params={}, user=self.user), action="list"
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


class DynamicFieldsMixinTestCase(TestCase):
    def setUp(self):
        self.viewset_class = PartyViewSet
        self.serializer_class = PartySerializer
        self.user = Person.objects.create()
        self.party = Party.objects.create(title="foo", host=self.user)
        self.invite = Invite.objects.create(
            text="foo", party=self.party, sender=self.user, recipient=self.user
        )
        self.answer = Answer.objects.create(text="foo", invite=self.invite)
        self.details = Details.objects.create(answer=self.answer, reviewer=self.user)

    def test_empty_fields(self):
        query_params = {"fields": "id,title,invites"}
        viewset = self.viewset_class(
            request=MockRequest(query_params=query_params),
            action="retrieve",
            format_kwarg="json",
        )
        serializer = viewset.get_serializer(self.party)
        self.assertEqual(
            {"id": self.party.pk, "title": self.party.title}, serializer.data
        )

    def test_pk_only_optimization(self):
        query_params = {"fields": "id,host.id"}
        viewset = self.viewset_class(
            request=MockRequest(query_params=query_params),
            action="retrieve",
            format_kwarg="json",
        )
        serializer = viewset.get_serializer(viewset.get_queryset().get())
        with self.assertNumQueries(0):
            serializer.data

    def test_representation(self):
        for query_params, representation in (
            (
                {"fields": "host.id,invites.answer.id"},
                {
                    "host": {"id": self.user.pk},
                    "invites": [{"answer": {"id": self.answer.pk}}],
                },
            ),
            (
                {"fields": "host.id,host.name,invites.answer.id"},
                {
                    "host": {"id": self.user.pk, "name": self.user.name},
                    "invites": [{"answer": {"id": self.answer.pk}}],
                },
            ),
            (
                {"fields": "host.id,host.name,invites_count"},
                {
                    "host": {"id": self.user.pk, "name": self.user.name},
                    "invites_count": 1,
                },
            ),
            (
                {
                    "fields": "invites.answer.all_details_reviewed,"
                    "invites.answer.details.reviewer.id"
                },
                {
                    "invites": [
                        {
                            "answer": {
                                "all_details_reviewed": False,
                                "details": [{"reviewer": {"id": self.user.pk}}],
                            }
                        }
                    ]
                },
            ),
        ):
            for many in (True, False):
                viewset = self.viewset_class(
                    request=MockRequest(query_params=query_params, user=self.user),
                    action="retrieve",
                    format_kwarg="json",
                )
                if many:
                    queryset = viewset.get_queryset()
                    serializer = viewset.get_serializer(queryset, many=True)
                    data = [representation]
                else:
                    instance = viewset.get_queryset().get()
                    serializer = viewset.get_serializer(instance)
                    data = representation
                self.assertEqual(data, serializer.data)
