from users.serializers import UserSerializer
from .models import Conversation, Message
from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer
from django.db.models import Q
from django.shortcuts import redirect, reverse


@api_view(['POST'])
def start_conversation(request, username):
    """
    Start a conversation with the specified user.

    Parameters:
        request (HttpRequest): The HTTP request object.
        username (str): The username of the user to start a conversation with.

    Returns:
        Response: HTTP response with data indicating success or failure.
    """
    data = request.data
    try:
        participant = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'message': 'You cannot chat with a non-existent user'})

    conversation = Conversation.objects.filter(Q(initiator=request.user, receiver=participant) |
                                               Q(initiator=participant, receiver=request.user))
    if conversation.exists():
        return redirect(reverse('get_conversation', args=(conversation[0].id,)))
    else:
        conversation = Conversation.objects.create(initiator=request.user, receiver=participant)
        if 'message' in data:
            if 'text' not in data:
                return Response({'error': "You have to provide a message text"}, status=400)
            if 'receiver' not in data:
                return Response({'error': "You have to provide receiver username"}, status=400)
            Message.objects.create(sender=request.user, text=data['text'], conversation=conversation)
        return Response(ConversationSerializer(instance=conversation).data)


@api_view(['GET'])
def get_conversation(request, convo_id):
    """
    Retrieve a conversation by its ID.

    Parameters:
        request (HttpRequest): The HTTP request object.
        convo_id (int): The ID of the conversation to retrieve.

    Returns:
        Response: HTTP response with the serialized conversation data.
    """
    conversation = Conversation.objects.filter(id=convo_id)
    if not conversation.exists():
        return Response({'message': 'Conversation does not exist'})
    else:
        serializer = ConversationSerializer(instance=conversation[0], context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
def conversations(request):
    """
    Retrieve a list of conversations involving the current user.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        Response: HTTP response with the serialized list of conversations.
    """
    conversation_list = Conversation.objects.filter(Q(initiator=request.user) |
                                                    Q(receiver=request.user))
    serializer = ConversationListSerializer(conversation_list, many=True, context={'request': request})
    return Response(serializer.data)
