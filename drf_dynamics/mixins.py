import copy

from django.db import models
from django.utils.functional import cached_property
from rest_framework.relations import RelatedField

from .helpers import get_deep, set_deep, tagged_chain


class DynamicSerializerClassMixin:
    dynamic_serializer_class = {}

    def get_serializer_class(self):
        return self.dynamic_serializer_class.get(self.action, self.serializer_class)


class DynamicPermissionClassesMixin:
    dynamic_permission_classes = {}

    def get_permissions(self):
        return [
            permission()
            for permission in self.dynamic_permission_classes.get(
                self.action, self.permission_classes
            )
        ]


class DynamicQuerySetMixin:
    dynamic_fields_actions = {
        "create",
        "list",
        "retrieve",
        "update",
        "partial_update",
    }
    dynamic_prefetches = {}
    dynamic_annotations = {}
    dynamic_selects = {}

    @cached_property
    def requested_fields(self):
        requested_fields = self.request.query_params.get("fields")
        if not requested_fields:
            return None
        ret = {}
        for path in requested_fields.lower().split(","):
            set_deep(ret, path, {})
        return ret

    def setup_dynamic_queryset(self, queryset):
        prefetches_map = {}
        allow_all_fields = self.requested_fields is None

        for tag, (path, spec) in tagged_chain(
            self.dynamic_prefetches.items(),
            self.dynamic_annotations.items(),
            self.dynamic_selects.items(),
            tag_names=("prefetch", "annotation", "select"),
        ):
            if not allow_all_fields:
                requested_slice = get_deep(self.requested_fields, path)
                if requested_slice is None:
                    continue
                # If the only field we're requesting is a pk,
                # we don't need to select it.
                # Make sure your serializer grabs the value smartly, though.
                if (
                    tag == "select"
                    and len(requested_slice) == 1
                    and spec.pk_field_name in requested_slice
                ):
                    continue

            if tag == "prefetch":
                prefetch_queryset = (
                    spec.get_queryset(self.request)
                    if spec.get_queryset is not None
                    else spec.queryset
                )
                prefetch = models.Prefetch(spec.lookup, prefetch_queryset, spec.to_attr)
                prefetches_map[path] = prefetch
                method = "prefetch_related"
                arg = prefetch
            elif tag == "annotation":
                method = spec.method_name
                arg = self.request
            else:
                method = "select_related"
                arg = spec.lookup

            if spec.parent_prefetch_path is not None:
                parent_prefetch = prefetches_map[spec.parent_prefetch_path]
                parent_prefetch.queryset = getattr(parent_prefetch.queryset, method)(
                    arg
                )
            else:
                queryset = getattr(queryset, method)(arg)

        return queryset

    def get_queryset(self,):
        queryset = super().get_queryset()
        if self.action in self.dynamic_fields_actions:
            queryset = self.setup_dynamic_queryset(queryset)
        return queryset

    def get_serializer(self, *args, **kwargs):
        if self.action in self.dynamic_fields_actions:
            kwargs["requested_fields"] = self.requested_fields
        return super().get_serializer(*args, **kwargs)


class DynamicFieldsMixin:
    pk_field_name = "id"
    representation_fields = {}

    def __init__(self, *args, **kwargs):
        self.requested_fields = kwargs.pop("requested_fields", None)
        super().__init__(*args, **kwargs)

    @staticmethod
    def use_pk_only_optimization():
        # For the hijacked RelatedField's `get_attribute`.
        return True

    def get_attribute(self, instance):
        # If the only field we need to represent is the `id`,
        # we should grab it in an optimized way,
        # to not trigger a query if it isn't selected.
        # For that we hijack the RelatedField's `get_attribute`.
        if (
            len(self._readable_fields) == 1
            and self._readable_fields[0].field_name == self.pk_field_name
        ):
            try:
                pk_only = RelatedField.get_attribute(self, instance)
                setattr(pk_only, self.pk_field_name, pk_only.pk)
                return pk_only
            # Will be raised in case of reverse OneToOneField.
            except TypeError:
                pass
        return super().get_attribute(instance)

    @staticmethod
    def representation_field_is_empty(representation_field):
        if hasattr(representation_field, "child"):
            representation_field = representation_field.child
        if hasattr(representation_field, "_readable_fields"):
            return (
                next((_ for _ in representation_field._readable_fields), None) is None
            )
        return False

    @cached_property
    def _readable_fields(self):
        base_fields = self.fields
        fields = {}
        representation_fields = copy.deepcopy(self.representation_fields)
        allow_all_fields = self.requested_fields is None

        for tag, (field_name, field) in tagged_chain(
            base_fields.items(),
            representation_fields.items(),
            tag_names=("base", "representation"),
        ):
            if allow_all_fields:
                if tag == "representation":
                    field.bind(field_name=field_name, parent=self)
                fields[field_name] = field
                continue

            if field_name not in self.requested_fields:
                continue

            if tag == "base":
                if field_name not in representation_fields:
                    fields[field_name] = field
                continue

            nested_fields = self.requested_fields[field_name]
            if hasattr(field, "child"):
                field.child.requested_fields = nested_fields
            else:
                field.requested_fields = nested_fields

            if self.representation_field_is_empty(field):
                continue

            field.bind(field_name=field_name, parent=self)
            fields[field_name] = field

        return [field for field in fields.values() if not field.write_only]
