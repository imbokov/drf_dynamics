# drf_dynamic

## Motivation

Handles the hassle of handling the amount of fields to be serialized and queryset changes for each request for you.

Example:

`GET /api/party/?fields=id,title`

`response`
```json
[
    {
        "id": 1,
        "title": "foo"
    },
    {
        "id": 2,
        "title": "bar"
    }
]
```

`sql`
```sql
SELECT
   "party_party"."id",
   "party_party"."title",
   "party_party"."host_id" 
FROM
   "party_party"
```

`GET /api/party/?fields=id,title,host.id,host.username`

`response`
```json
[
    {
        "id": 1,
        "title": "foo",
        "host": {
            "id": 1,
            "username": "root"
        }
    },
    {
        "id": 2,
        "title": "bar",
        "host": {
            "id": 1,
            "username": "root"
        }
    }
]
```

`sql`
```sql
SELECT
   "party_party"."id",
   "party_party"."title",
   "party_party"."host_id",
   "auth_user"."id",
   "auth_user"."username",
   "auth_user"."first_name",
   "auth_user"."last_name",
   "auth_user"."email",
   "auth_user"."is_staff",
   "auth_user"."is_active",
   "auth_user"."date_joined" 
FROM
   "party_party" 
   INNER JOIN
      "auth_user" 
      ON ("party_party"."host_id" = "auth_user"."id")
```

## Requirements

* Python >= 3.5
* Django >= 1.11
* DjangoRestFramework >= 3.7.0

## Installation

```
pip install drf_dynamics
```

## Usage

### DynamicQuerySetMixin

Usage example:
```python
class PartyViewSet(DynamicQuerySetMixin, ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
```

The only thing it does by default is parse the `fields` query parameter and pass it to the serializer. It **doesn't** modify the queryset **yet**. For that you'll need to use `dynamic_queryset` decorator (see below).
If you want to modify the actions, for which this should work, change the `dynamic_fields_actions` class attribute on the viewset:

*Note: it has to be a set*
```python
class PartyViewSet(DynamicQuerySetMixin, ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    dynamic_fields_actions = {"list"}
```
Default is:
```python
{
    "create",
    "list",
    "retrieve",
    "update",
    "partial_update",
}
```

### DynamicFieldsMixin

Usage example:
```python
class PartySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = (
            "id",
            "title",
            "host",
        )
```

Now, if the viewset passes the parsed requested fields to the serializer, the fields will change depending on the request.

#### representation_fields

You can specify additional fields by using the `representation_fields` attribute. Those will be read-only, will override default fields, and don't have to be specified in the `Meta.fields` attribute (useful if there's a chance those fields won't be present on the instance).

You can use serializers in those fields, that also inherit from `DynamicFieldsMixin` and nest those as much as you want.

Usage example:
```python
class PartySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = (
            "id",
            "title",
            "host",
        )

    representation_fields = {
        "host": PersonSerializer(),
        "invites": InviteSerializer(many=True),
        "invites_count": serializers.IntegerField(),
    }
```

### dynamic_queryset(prefetches, annotations, selects)

A viewset decorator that enables the dynamic queryset change depending on the request.

You have to specify all the `prefetch_related` and `select_related` lookups, and annotation queryset methods your serializer may require to render its fields using this decorator, which will allow for those modifications to be dynamically applied.

You **must** specify `queryset` on your viewset for this decorator to work.

Usage example:
```python
@dynamic_queryset(
    prefetches="invites",
    annotations="invites_count",
    selects=(
        "host",
        "invites.sender",
        "invites.recipient",
    ),
)
class PartyViewSet(DynamicQuerySetMixin, ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
```

Each parameter can accept either a single string or a sequence of strings.
The strings are then applied to their parent prefetch's queryset if there is one, or to the viewset's queryset otherwise.
In case of `prefetches` and `selects` the decorator assumes that the field's name corresponds to the queryset's `select_related` or `prefetch_related` lookup, where all the dots are converted to `__`.
For `annotations`, it will search for a method on the queryset that has a format of `with_{field_name}`. 
**Your queryset methods will receive `Request` object as the first argument**.

If that's not the case for you, you can override lookups and methods names by supplying a mapping either as an argument or the last element of the sequence which will be supplied as an argument:
```python
@dynamic_queryset(
    prefetches=(
        "invites",
        {"invites.answer": "response"},
    ),
    annotations={
        "invites_count": "invites_count",
    },
    selects=(
        "invites.sender",
        "invites.recipient",
        {"host": "user"},
    ),
)
class PartyViewSet(DynamicQuerySetMixin, ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
```
Keep in mind, that the specified lookup must be applied from the parent prefetch's queryset context if there is one, hence the `{"invites.answer": "response"}` line.

### DynamicPrefetch

If you need even more control over your prefetches, those can be applied using `DynamicPrefetch` instance. It accepts the same arguments as Django's `Prefetch` and works in the same way, but can also accept a callable instead of the `queryset` argument. The callable will be supplied with a `Request` object as its first argument.

Usage example:
```python
@dynamic_queryset(
    prefetches=(
        "invites.answer",
        "invites.answer.details",
        {"invites": DynamicPrefetch("invites", Invite.objects.for_user)},
    ),
    ...
)
class PartyViewSet(DynamicQuerySetMixin, ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
```

The callable not necessarily has to be a queryset method. Any callable which accepts one argument and returns an appropriate queryset will do.
