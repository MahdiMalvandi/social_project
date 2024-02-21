from users.serializers import UserSerializer
from .models import Conversation, Message
from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer
from django.db.models import Q
from django.shortcuts import redirect, reverse


# Create your views here.
@api_view(['POST'])
def start_conversation(request, username):
    data = request.data
    try:
        participant = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'message': 'You cannot chat with a non existent user'})

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
    conversation = Conversation.objects.filter(id=convo_id)
    if not conversation.exists():
        return Response({'message': 'Conversation does not exist'})
    else:
        serializer = ConversationSerializer(instance=conversation[0], context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
def conversations(request):
    conversation_list = Conversation.objects.filter(Q(initiator=request.user) |
                                                    Q(receiver=request.user))
    print(conversation_list)
    serializer = ConversationListSerializer(conversation_list, many=True)
    return Response(serializer.data)
