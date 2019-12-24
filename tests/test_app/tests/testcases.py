from rest_framework.test import APITestCase

from drf_dynamics.specs import DynamicPrefetch


class TestCase(APITestCase):
    def assertQuerysetsEqual(self, qs, other):
        """
        Only works if prefetches are not strings and have querysets.
        """
        self.assertEqual(str(qs.query), str(other.query))
        self.assertEqual(
            len(qs._prefetch_related_lookups), len(other._prefetch_related_lookups)
        )
        for qs_prefetch, other_prefetch in zip(
            qs._prefetch_related_lookups, other._prefetch_related_lookups
        ):
            self.assertEqual(
                qs_prefetch.prefetch_through, other_prefetch.prefetch_through
            )
            self.assertEqual(qs_prefetch.prefetch_to, other_prefetch.prefetch_to)
            self.assertQuerysetsEqual(qs_prefetch.queryset, other_prefetch.queryset)
            self.assertEqual(qs_prefetch.to_attr, other_prefetch.to_attr)

    def assertSpecsEqual(self, spec, other):
        self.assertIs(type(spec), type(other))
        self.assertEqual(
            {key: value for key, value in spec.__dict__.items() if key != "queryset"},
            {key: value for key, value in other.__dict__.items() if key != "queryset"},
        )
        if isinstance(spec, DynamicPrefetch):
            self.assertQuerysetsEqual(spec.queryset, other.queryset)
