from drf_dynamics.helpers import dynamic_queryset, tagged_chain
from drf_dynamics.specs import DynamicAnnotation, DynamicPrefetch, DynamicSelect
from tests.test_app.models import Answer, Details, Invite, Party
from tests.test_app.tests.testcases import TestCase


class TaggedChainTestCase(TestCase):
    def test_regular(self):
        gen = tagged_chain((1, 2), (3, 4), (5, 6))
        self.assertEqual((0, 1), next(gen))
        self.assertEqual((0, 2), next(gen))
        self.assertEqual((1, 3), next(gen))
        self.assertEqual((1, 4), next(gen))
        self.assertEqual((2, 5), next(gen))
        self.assertEqual((2, 6), next(gen))

    def test_tag_names(self):
        gen = tagged_chain(
            (1, 2), (3, 4), (5, 6), tag_names=("first", "second", "third")
        )
        self.assertEqual(("first", 1), next(gen))
        self.assertEqual(("first", 2), next(gen))
        self.assertEqual(("second", 3), next(gen))
        self.assertEqual(("second", 4), next(gen))
        self.assertEqual(("third", 5), next(gen))
        self.assertEqual(("third", 6), next(gen))

    def test_empty_iterables(self):
        gen = tagged_chain((1, 2), (), (), (3, 4))
        self.assertEqual((0, 1), next(gen))
        self.assertEqual((0, 2), next(gen))
        self.assertEqual((3, 3), next(gen))
        self.assertEqual((3, 4), next(gen))


class DynamicQuerySetTestCase(TestCase):
    def setUp(self):
        class ViewSet:
            queryset = Party.objects.all()

        self.viewset_class = ViewSet

    def test_simple_lookups(self):
        prefetches = "invites"
        annotations = ("invites_count", "invites.has_answer")
        selects = ("host", "invites.sender", "invites.recipient", "invites.answer")

        dynamic_queryset(
            prefetches=prefetches, annotations=annotations, selects=selects
        )(self.viewset_class)

        self.assertEqual(1, len(self.viewset_class.dynamic_prefetches))
        self.assertSpecsEqual(
            DynamicPrefetch("invites", Invite.objects.all()),
            self.viewset_class.dynamic_prefetches["invites"],
        )

        self.assertEqual(2, len(self.viewset_class.dynamic_annotations))
        self.assertSpecsEqual(
            DynamicAnnotation("with_invites_count"),
            self.viewset_class.dynamic_annotations["invites_count"],
        )
        self.assertSpecsEqual(
            DynamicAnnotation("with_has_answer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_annotations["invites.has_answer"],
        )

        self.assertEqual(4, len(self.viewset_class.dynamic_selects))
        self.assertSpecsEqual(
            DynamicSelect("host"), self.viewset_class.dynamic_selects["host"],
        )
        self.assertSpecsEqual(
            DynamicSelect("sender", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.sender"],
        )
        self.assertSpecsEqual(
            DynamicSelect("recipient", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.recipient"],
        )
        self.assertSpecsEqual(
            DynamicSelect("answer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.answer"],
        )

    def test_mappings(self):
        def get_invites(request):
            return Invite.objects.for_user(request.user)

        prefetches = {
            "invites": DynamicPrefetch("invites", get_invites),
            "invites.answers": DynamicPrefetch("answer", Answer.objects.all()),
            "invites.answers.details": DynamicPrefetch(
                "details", Details.objects.all()
            ),
            "invites.answers.unreviewed_details": DynamicPrefetch(
                "details",
                Details.objects.filter(reviewed=False),
                to_attr="unreviewed_details",
            ),
        }
        annotations = (
            "invites_count",
            {
                "invites.has_answer": "has_answer",
                "invites.answers.all_details_reviewed": "details_reviewed",
            },
        )
        selects = (
            "host",
            "invites.sender",
            "invites.recipient",
            {"invites.answers.person_who_reviewed": "reviewer"},
        )

        dynamic_queryset(
            prefetches=prefetches, annotations=annotations, selects=selects
        )(self.viewset_class)

        self.assertEqual(4, len(self.viewset_class.dynamic_prefetches))
        prefetch_to_compare = DynamicPrefetch("invites", get_invites)
        prefetch_to_compare.queryset = Invite.objects.all()
        self.assertSpecsEqual(
            prefetch_to_compare, self.viewset_class.dynamic_prefetches["invites"],
        )
        self.assertSpecsEqual(
            DynamicPrefetch(
                "answer", Answer.objects.all(), parent_prefetch_path="invites"
            ),
            self.viewset_class.dynamic_prefetches["invites.answers"],
        )
        self.assertSpecsEqual(
            DynamicPrefetch(
                "details", Details.objects.all(), parent_prefetch_path="invites.answers"
            ),
            self.viewset_class.dynamic_prefetches["invites.answers.details"],
        )
        self.assertSpecsEqual(
            DynamicPrefetch(
                "details",
                Details.objects.filter(reviewed=False),
                to_attr="unreviewed_details",
                parent_prefetch_path="invites.answers",
            ),
            self.viewset_class.dynamic_prefetches["invites.answers.unreviewed_details"],
        )

        self.assertEqual(3, len(self.viewset_class.dynamic_annotations))
        self.assertSpecsEqual(
            DynamicAnnotation("with_invites_count"),
            self.viewset_class.dynamic_annotations["invites_count"],
        )
        self.assertSpecsEqual(
            DynamicAnnotation("has_answer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_annotations["invites.has_answer"],
        )
        self.assertSpecsEqual(
            DynamicAnnotation(
                "details_reviewed", parent_prefetch_path="invites.answers"
            ),
            self.viewset_class.dynamic_annotations[
                "invites.answers.all_details_reviewed"
            ],
        )

        self.assertEqual(4, len(self.viewset_class.dynamic_selects))
        self.assertSpecsEqual(
            DynamicSelect("host"), self.viewset_class.dynamic_selects["host"],
        )
        self.assertSpecsEqual(
            DynamicSelect("sender", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.sender"],
        )
        self.assertSpecsEqual(
            DynamicSelect("recipient", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.recipient"],
        )
        self.assertSpecsEqual(
            DynamicSelect("reviewer", parent_prefetch_path="invites.answers"),
            self.viewset_class.dynamic_selects["invites.answers.person_who_reviewed"],
        )

    def test_select_chaining(self):
        prefetches = "invites"
        selects = "invites.answer.reviewer"

        dynamic_queryset(prefetches=prefetches, selects=selects)(self.viewset_class)

        self.assertSpecsEqual(
            DynamicSelect("answer__reviewer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.answer.reviewer"],
        )
