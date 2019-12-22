from rest_framework.test import APITestCase

from drf_dynamics.specs import DynamicPrefetch


class TestCase(APITestCase):
    def assertQuerysetsEqual(self, qs, other):
        return self.assertEqual(str(qs.query), str(other.query))

    def assertSpecsEqual(self, spec, other):
        result = type(spec) is type(other) and {
            key: value for key, value in spec.__dict__.items() if key != "queryset"
        } == {key: value for key, value in other.__dict__.items() if key != "queryset"}
        if isinstance(spec, DynamicPrefetch):
            return result and self.assertQuerysetsEqual(spec.queryset, other.queryset)
        return result
