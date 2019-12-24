import itertools
from collections import Collection, Mapping, OrderedDict, Sequence

from .specs import DynamicAnnotation, DynamicPrefetch, DynamicSelect, DynamicSpec


def tagged_chain(*iterables, tag_names=None):
    """
    An itertools.chain modification,
    that yields tuples of `tag, item` of supplied iterables.
    Main caveat is that iterables MUST be sized, or it wouldn't work.
    Supply `tag_names` tuple as a keyword argument,
    where the names are in the same positions as iterables, to have the tags named.
    """
    assert all(
        isinstance(iterable, Collection) for iterable in iterables
    ), "Supplied iterables have to be a Collection"
    assert (
        isinstance(tag_names, Sequence) if tag_names is not None else True
    ), "tag_names should be a Sequence"
    assert (
        len(iterables) == len(tag_names) if tag_names is not None else True
    ), "The amount of iterables supplied doesn't match the tag_names"

    def get_meta():
        lengths_sum = 0
        for iterable_index, iterable in enumerate(iterables):
            length = len(iterable)
            if length == 0:
                continue
            lengths_sum += length
            yield iterable_index, lengths_sum

    meta = get_meta()
    tag = current_length = 0

    for index, item in enumerate(itertools.chain(*iterables)):
        if index == current_length:
            tag, current_length = next(meta)
            if tag_names is not None:
                tag = tag_names[tag]
        yield tag, item


def set_deep(instance, path, value):
    """
    Do NOT use this helper in your code.
    It's extremely primitive and wouldn't work properly with most Mappings.
    """
    path = path.split(".")
    for path_segment in path[:-1]:
        if path_segment not in instance:
            instance[path_segment] = {}
        instance = instance[path_segment]
    instance[path[-1]] = value


def get_deep(instance, path):
    """
    Do NOT use this helper in your code.
    It's extremely primitive and wouldn't work properly with most Mappings.
    """
    path = path.split(".")
    for path_segment in path:
        if path_segment not in instance:
            return None
        instance = instance[path_segment]
    return instance


def dynamic_queryset(prefetches=None, annotations=None, selects=None):
    def parse_spec(spec):
        if not spec:
            return {}

        sequence_to_merge = ()
        mapping_to_merge = {}
        if isinstance(spec, str):
            sequence_to_merge = (spec,)
        elif isinstance(spec, Mapping):
            mapping_to_merge = spec
        elif isinstance(spec, Sequence):
            if isinstance(spec[-1], Mapping):
                sequence_to_merge = spec[:-1]
                mapping_to_merge = spec[-1]
            else:
                sequence_to_merge = spec
        return OrderedDict(
            sorted(
                {
                    **{path: None for path in sequence_to_merge},
                    **mapping_to_merge,
                }.items()
            )
        )

    def find_parent_prefetch_path(prefetches_map, path):
        while path.count(".") != 0:
            path = path.rsplit(".", 1)[0]
            if path in prefetches_map:
                return path
        return None

    def determine_queryset(parent_queryset, lookup):
        model = parent_queryset.model._meta.get_field(lookup).related_model
        return model._meta.default_manager.all()

    def wrapper(klass):
        root_queryset = klass.queryset
        prefetches_map = {}
        annotations_map = {}
        selects_map = {}
        tag_to_class = {
            "prefetch": DynamicPrefetch,
            "annotation": DynamicAnnotation,
            "select": DynamicSelect,
        }
        tag_to_map = {
            "prefetch": prefetches_map,
            "annotation": annotations_map,
            "select": selects_map,
        }
        for tag, (path, spec) in tagged_chain(
            parse_spec(prefetches).items(),
            parse_spec(annotations).items(),
            parse_spec(selects).items(),
            tag_names=("prefetch", "annotation", "select"),
        ):
            parent_prefetch_path = find_parent_prefetch_path(prefetches_map, path)
            if not isinstance(spec, DynamicSpec):
                if spec is None:
                    # In this branch we assume the lookup for selects and prefetches
                    # and method name for annotations if we weren't supplied a mapping.
                    if parent_prefetch_path:
                        # The lookup should start from the parent prefetch,
                        # if there is one.
                        spec = path[len(parent_prefetch_path) + 1 :]
                    else:
                        spec = path
                    if tag == "annotation":
                        spec = f"with_{spec}"
                    else:
                        spec = spec.replace(".", "__")
                spec = tag_to_class[tag](spec)
            spec.parent_prefetch_path = parent_prefetch_path
            if tag == "prefetch" and spec.queryset is None:
                parent_queryset = (
                    root_queryset
                    if parent_prefetch_path is None
                    else prefetches_map[parent_prefetch_path].queryset
                )
                spec.queryset = determine_queryset(parent_queryset, spec.lookup)
            tag_to_map[tag][path] = spec

        klass.dynamic_prefetches = prefetches_map
        klass.dynamic_annotations = annotations_map
        klass.dynamic_selects = selects_map

        return klass

    return wrapper
