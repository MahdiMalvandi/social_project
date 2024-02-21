from users.serializers import UserSerializer
from .models import Conversation, Message
from rest_framework import serializers


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    sent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('timestamp', 'text', 'sender', 'sent')

    def get_sent(self, instance):
        if instance.sender == self.context['request'].user:
            return True
        else:
            return False


class ConversationListSerializer(serializers.ModelSerializer):
    initiator = UserSerializer()
    receiver = UserSerializer()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['initiator', 'receiver', 'last_message', 'id']
        extra_kwargs = {'id': {'read_only': True}}

    def get_last_message(self, instance):
        message = instance.messages.first()
        print(message)
        return MessageSerializer(message).data


class ConversationSerializer(serializers.ModelSerializer):
    initiator = UserSerializer()
    receiver = UserSerializer()
    messages = MessageSerializer(many=True)


    class Meta:
        model = Conversation
        fields = ['initiator', 'receiver', 'messages']


