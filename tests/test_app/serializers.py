from rest_framework import serializers

from drf_dynamics.mixins import DynamicFieldsMixin
from .models import Answer, Details, Invite, Party, Person


class PersonSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            "id",
            "name",
        )


class DetailsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Details
        fields = (
            "id",
            "reviewer",
            "reviewed",
        )

    representation_fields = {
        "reviewer": PersonSerializer(),
    }


class AnswerSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = (
            "id",
            "text",
            "details",
        )

    representation_fields = {
        "details": DetailsSerializer(many=True),
        "all_details_reviewed": serializers.BooleanField(),
    }


class InviteSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = (
            "id",
            "text",
            "sender",
            "recipient",
            "answer",
        )

    representation_fields = {
        "sender": PersonSerializer(),
        "recipient": PersonSerializer(),
        "answer": AnswerSerializer(),
    }


class PartySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = (
            "id",
            "title",
            "host",
            "invites",
        )

    representation_fields = {
        "host": PersonSerializer(),
        "invites": InviteSerializer(many=True),
        "invites_count": serializers.IntegerField(),
    }
