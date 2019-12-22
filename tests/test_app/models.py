from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=255)


class Party(models.Model):
    title = models.CharField(max_length=255)
    host = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="hosted_parties"
    )


class Invite(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="invites")
    sender = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="sent_invites"
    )
    recipient = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="received_invites"
    )
    text = models.TextField()


class Answer(models.Model):
    invite = models.OneToOneField(
        Invite, on_delete=models.CASCADE, related_name="answer"
    )
    text = models.TextField()
