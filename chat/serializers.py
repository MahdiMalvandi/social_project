from users.serializers import UserSerializer
from .models import Conversation, Message
from rest_framework import serializers


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.

    This serializer handles the serialization/deserialization of Message objects.

    Attributes:
        sender: A nested representation of the sender user.
        sent: A boolean field indicating whether the message was sent by the requesting user.
    """

    sender = UserSerializer()
    sent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('timestamp', 'text', 'sender', 'sent')

    def get_sent(self, instance):
        """
        Get whether the message was sent by the requesting user.

        Args:
            instance: The Message instance being serialized.

        Returns:
            bool: True if the message was sent by the requesting user, False otherwise.
        """
        if instance.sender == self.context['user']:
            return True
        else:
            return False


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model used in list view.

    This serializer serializes Conversation objects for list view, including details of the last message.

    Attributes:
        initiator: A nested representation of the conversation initiator user.
        receiver: A nested representation of the conversation receiver user.
        last_message: A representation of the last message in the conversation.
    """

    initiator = UserSerializer()
    receiver = UserSerializer()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['initiator', 'receiver', 'last_message', 'id']
        extra_kwargs = {'id': {'read_only': True}}

    def get_last_message(self, instance):
        """
        Get the last message in the conversation.

        Args:
            instance: The Conversation instance being serialized.

        Returns:
            dict: Serialized representation of the last message.
        """
        message = instance.messages.first()
        return MessageSerializer(message, context={'user': self.context['request'].user}).data


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model used in detail view.

    This serializer serializes Conversation objects for detail view, including all messages.

    Attributes:
        initiator: A nested representation of the conversation initiator user.
        receiver: A nested representation of the conversation receiver user.
        messages: A representation of all messages in the conversation.
    """

    initiator = UserSerializer()
    receiver = UserSerializer()
    messages = MessageSerializer(many=True)

    class Meta:
        model = Conversation
        fields = ['initiator', 'receiver', 'messages']
