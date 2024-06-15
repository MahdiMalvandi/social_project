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
def add_message(request, username):
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

    conversations = Conversation.objects.filter(Q(initiator=request.user, receiver=participant) |
                                               Q(initiator=participant, receiver=request.user))
    if not conversations.exists():
        conversation = Conversation.objects.create(initiator=request.user, receiver=participant)
    else:
        conversation = conversations.first()
    if 'message' in data:
        message_data = data.get('message')
        Message.objects.create(sender=request.user, text=message_data, conversation=conversation)
    return Response(ConversationSerializer(instance=conversation, context={'request':request}).data, status=status.HTTP_200_OK)

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
def get_conversation(request, username):
    """
    Retrieve a conversation by its ID.

    Parameters:
        request (HttpRequest): The HTTP request object.
        convo_id (int): The ID of the conversation to retrieve.

    Returns:
        Response: HTTP response with the serialized conversation data.
    """
    data = request.data
    try:
        participant = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'message': 'You cannot chat with a non-existent user'}, status=status.HTTP_400_BAD_REQUEST)

    conversations = Conversation.objects.filter(Q(initiator=request.user, receiver=participant) |
                                               Q(initiator=participant, receiver=request.user))
    conversation = conversations.first()
    if not conversations.exists():
        return Response({'message': 'Conversation does not exist'})
    else:
        serializer = ConversationSerializer(instance=conversation, context={'request': request})
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


@api_view(['DELETE'])
def delete_message(request, id):
    messages = Message.objects.filter(id=id)
    if not messages.exists():
        return Response({'error': "A message with this id does not exists"}, status=status.HTTP_404_NOT_FOUND)
    message = messages.first()
    message.delete()
    return Response({'success': True}, status.HTTP_200_OK)


