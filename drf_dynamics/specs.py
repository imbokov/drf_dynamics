class DynamicSpec:
    def __init__(self):
        self.parent_prefetch_path = None


class DynamicAnnotation(DynamicSpec):
    def __init__(self, method_name):
        super().__init__()
        self.method_name = method_name


class DynamicSelect(DynamicSpec):
    def __init__(self, lookup, pk_field_name="id"):
        super().__init__()
        self.lookup = lookup
        self.pk_field_name = pk_field_name


class DynamicPrefetch(DynamicSpec):
    def __init__(self, lookup, queryset=None, to_attr=None):
        super().__init__()
        self.lookup = lookup
        if callable(queryset):
            self.queryset = None
            self.get_queryset = queryset
        else:
            self.queryset = queryset
            self.get_queryset = None
        self.to_attr = to_attr
