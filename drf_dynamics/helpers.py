import itertools
from operator import itemgetter

from .specs import DynamicAnnotation, DynamicPrefetch, DynamicSelect, DynamicSpec


def tagged_chain(*sequences, tag_names=None):
    def get_meta():
        length_sum = 0
        for sequence_index, sequence in enumerate(sequences):
            length = len(sequence)
            if length == 0:
                continue
            length_sum += length
            yield sequence_index, length_sum

    meta = get_meta()
    tag = current_length = 0

    for index, item in enumerate(itertools.chain(*sequences)):
        if index == current_length:
            tag, current_length = next(meta)
            if tag_names is not None:
                tag = tag_names[tag]
        yield tag, item


def set_deep(instance, path, value):
    path = path.split(".")
    for path_segment in path[:-1]:
        if path_segment not in instance:
            instance[path_segment] = {}
        instance = instance[path_segment]
    instance[path[-1]] = value


def get_deep(instance, path):
    path = path.split(".")
    for path_segment in path:
        if path_segment in instance:
            instance = instance[path_segment]
        else:
            return None
    return instance


def dynamic_queryset(prefetches=None, annotations=None, selects=None):
    def parse_spec(spec):
        if not spec:
            return {}

        sequences_to_merge = ()
        dict_to_merge = {}
        if isinstance(spec, str):
            sequences_to_merge = (spec,)
        elif isinstance(spec, dict):
            dict_to_merge = spec
        elif isinstance(spec[-1], dict):
            sequences_to_merge = spec[:-1]
            dict_to_merge = spec[-1]
        else:
            sequences_to_merge = spec
        return dict(
            sorted(
                {
                    **{path: None for path in sequences_to_merge},
                    **dict_to_merge,
                }.items(),
                key=itemgetter(0),
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
                    if parent_prefetch_path:
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
                spec.queryset = determine_queryset(
                    prefetches_map[parent_prefetch_path].queryset
                    if parent_prefetch_path is not None
                    else root_queryset,
                    spec.lookup,
                )
            tag_to_map[tag][path] = spec

        klass.dynamic_prefetches = prefetches_map
        klass.dynamic_annotations = annotations_map
        klass.dynamic_selects = selects_map

        return klass

    return wrapper
