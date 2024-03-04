from rest_framework import status

from users.serializers import UserSerializer
from .models import Conversation, Message
from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer
from django.db.models import Q
from django.shortcuts import redirect, reverse

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(
    method='post',
    operation_description="Start a conversation with the specified user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'text': openapi.Schema(type=openapi.TYPE_STRING)
                },
                required=[]
            )
        }
    ),
    responses={
        200: openapi.Response(description="Conversation started successfully.", schema=ConversationSerializer),
        400: "Invalid input or missing required field.",
        302: "Redirects to the conversation page if a conversation with the user already exists."
    }
)
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
        return Response({'message': 'You cannot chat with a non-existent user'}, status=status.HTTP_400_BAD_REQUEST)

    conversation = Conversation.objects.filter(Q(initiator=request.user, receiver=participant) |
                                               Q(initiator=participant, receiver=request.user))
    if conversation.exists():
        return redirect(reverse('get_conversation', args=(conversation[0].id,)))
    else:
        conversation = Conversation.objects.create(initiator=request.user, receiver=participant)
        if 'message' in data:
            message_data = data.get('message')
            if 'text' in message_data:
                Message.objects.create(sender=request.user, text=message_data['text'], conversation=conversation)
        return Response(ConversationSerializer(instance=conversation).data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a conversation by its ID.",
    manual_parameters=[
        openapi.Parameter('convo_id', openapi.IN_PATH, description="The ID of the conversation to retrieve.", type=openapi.TYPE_INTEGER)
    ],
    responses={200: openapi.Response(description="Conversation data", schema=ConversationSerializer),
               404: "Conversation id is wrong"},
)
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


@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a list of conversations involving the current user.",
    responses={200: openapi.Response(description="List of conversations", schema=ConversationListSerializer)},
)
@api_view(['GET'])
def conversations(request):
    """
    Retrieve a list of conversations involving the current user.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        Response: HTTP response with the serialized list of conversations.
    """
    conversation_list = Conversation.objects.filter(Q(initiator=request.user) | Q(receiver=request.user))
    serializer = ConversationListSerializer(conversation_list, many=True, context={'request': request})
    return Response(serializer.data)
