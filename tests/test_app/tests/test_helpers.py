from unittest import TestCase

from drf_dynamics.helpers import tagged_chain


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
