from django.db import models

from .managers import AnswerManager, InviteManager, PartyManager


class Person(models.Model):
    name = models.CharField(max_length=255)


class Party(models.Model):
    title = models.CharField(max_length=255)
    host = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="hosted_parties"
    )

    objects = PartyManager()


class Invite(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="invites")
    sender = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="sent_invites"
    )
    recipient = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="received_invites"
    )
    text = models.TextField()

    objects = InviteManager()


class Answer(models.Model):
    invite = models.OneToOneField(
        Invite, on_delete=models.CASCADE, related_name="answer"
    )
    text = models.TextField()

    objects = AnswerManager()


class Details(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="details")
    reviewer = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="reviewed_details"
    )
    reviewed = models.BooleanField(default=False)
