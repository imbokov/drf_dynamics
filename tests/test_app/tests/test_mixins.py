from .helpers import MockRequest
from .testcases import TestCase
from ..views import PartyViewSet


class DynamicQuerySetMixinTestCase(TestCase):
    def setUp(self):
        self.viewset_class = PartyViewSet

    def test_requested_fields_cached(self):
        viewset = self.viewset_class(request=MockRequest(query_params={"foo": "bar"}))
        first_fields = viewset.requested_fields
        viewset.request.query_params["bar"] = ["baz"]
        self.assertIs(first_fields, viewset.requested_fields)
