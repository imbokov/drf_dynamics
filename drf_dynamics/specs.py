class DynamicSpec:
    def __init__(self, parent_prefetch_path=None):
        self.parent_prefetch_path = parent_prefetch_path


class DynamicAnnotation(DynamicSpec):
    def __init__(self, method_name, **kwargs):
        super().__init__(**kwargs)
        self.method_name = method_name


class DynamicSelect(DynamicSpec):
    def __init__(self, lookup, pk_field_name="id", **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.pk_field_name = pk_field_name


class DynamicPrefetch(DynamicSpec):
    def __init__(self, lookup, queryset=None, to_attr=None, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        if callable(queryset):
            self.queryset = None
            self.get_queryset = queryset
        else:
            self.queryset = queryset
            self.get_queryset = None
        self.to_attr = to_attr
