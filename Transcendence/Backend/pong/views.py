from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.exceptions import ValidationError

import logging
import random  # For simulating matchmaking

from .forms import RegistrationForm, ProfileForm
from .models import Profile, GameServerModel, WaitingPlayerModel
from django.db.models import Q

from .serializers import UserRegisterSerializer, UserLoginSerializer
from .utils import custom_validation, valid_email, valid_password, create_user_token, ManageGameQueue
import json

UserModel = get_user_model()
logger = logging.getLogger(__name__)

# Register new user
class UserRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Clean data using the custom validation function
        try:
            clean_data = custom_validation(request.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Serialize and save user data
        serializer = UserRegisterSerializer(data=clean_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()  # save() calls create() in the serializer
            return Response({
                "message": "User successfully registered",
                "user": {
                    "username": user.username,
                    "email": user.email,
                },
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login user and generate JWT token
class UserLogin(APIView):
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        data = request.data
        identifier = data.get("identifier")  # Use identifier for email or username
        password = data.get("password")
        
        # Log identifier and password for debugging
        logger.info(f"!!!!!!!!!!!!!!!!!!!!identifier is : {identifier}")
        logger.info(f"!!!!!!!!!!!!!!!!!!!!password is : {password}")
        
        # Check if identifier and password are provided
        if not identifier or not password:
            return Response({"error": "Identifier and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Attempt to retrieve user by email or username
        try:
            user = UserModel.objects.get(Q(email=identifier) | Q(username=identifier))
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check password correctness
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate the JWT tokens (access and refresh)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Add `user_id` to the access token 
        refresh.access_token["user_id"] = user.id

        # Set user to online (if your app has an 'isOnline' field in the profile model)
        if hasattr(user, 'profile'):
            user.profile.isOnline = True
            user.profile.save()

        return Response({
            "access": access_token,
            "refresh": refresh_token
        }, status=status.HTTP_200_OK)


# Logout user and update online status

class UserLogout(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated with JWT

    def post(self, request):
        # Get the JWT token from the request headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response({'error': 'Authorization header missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Extract the token (it will be in the form of "Bearer <token>")
        token = auth_header.split(' ')[1]

        try:
            # Decode the token to get the user
            access_token = AccessToken(token)
            user_id = access_token["user_id"]  # Get the user_id from the token

            # Log the extracted user_id to check if it's correct
            logger.info(f"Extracted user_id: {user_id}")

            # Retrieve the user object using the user_id
            user_obj = UserModel.objects.get(pk=user_id)
            if user_obj.profile:
                user_obj.profile.isOnline = False  # Set user to offline
                user_obj.profile.save()

            # Successfully logged out
            logger.info(f"User {user_obj.username} logged out successfully.")

        except Exception as e:
            # Log the error message for debugging
            logger.error(f"Error during logout: {e}")
            return Response({'error': 'Failed to logout or user not found'}, status=status.HTTP_404_NOT_FOUND)

        # Log out the user from the session
        logout(request)
        return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def some_protected_view(request):
    # This view requires the user to be authenticated with a JWT token
    return Response({'message': 'You have access to this view.'})

@login_required
def pong(request):
    return render(request, 'index.html')


@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'profile.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile view
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})



# # This will hold your matchmaking queue
# matchmaking_queue = []

# @api_view(['POST'])
# async def matchmaking(request):
#     user_id = request.data.get('user_id')
#     matchmaking_queue.append(user_id)

#     if len(matchmaking_queue) >= 2:
#         player1_id = matchmaking_queue.pop(0)
#         player2_id = matchmaking_queue.pop(0)

#         player1 = Profile.objects.get(user_id=player1_id)
#         player2 = Profile.objects.get(user_id=player2_id)

#         # Return the nicknames instead of just user IDs
#         return Response({
#             'message': 'Match found',
#             'players': [player1.nickname, player2.nickname]
#         })

#     return Response({'message': 'Waiting for another player...'})

class JoinQueue(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Extract the JWT token from the Authorization header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1] if auth_header and " " in auth_header else None
        
        # Decode the token to get the user_id
        validated_token = JWTAuthentication().get_validated_token(token)
        user_id = validated_token['user_id']  # Extract user_id from the token payload
        
        # Add player to waiting queue using the extracted user_id
        WaitingPlayerModel.objects.create(player_id=user_id)
        
        return Response({'message': 'You have joined the queue.'}, status=status.HTTP_200_OK)


class CheckJoinGame(APIView):
    permission_classes = (permissions.AllowAny,)


    def post(self, request):
        # Initialize logging
        logger = logging.getLogger(__name__)
        
        # Manage the game queue
        ManageGameQueue()

        # Extract JWT token from Authorization header
        auth_header = request.headers.get('Authorization')

        token = auth_header.split(" ")[1] if auth_header and " " in auth_header else None

        # Decode the token to get the user_id
        validated_token = JWTAuthentication().get_validated_token(token)
        user_id = validated_token['user_id']

        # Query the GameServerModel to check if the user is in an existing game
        game_server = GameServerModel.objects.filter(Q(firstPlayerId=user_id) | Q(secondPlayerId=user_id)).first()
        
        # Check game state and return appropriate response
        if game_server:
            if game_server.state == 'full':
                return Response({'gameId': game_server.serverId}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Searching for a game.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Searching for a game.'}, status=status.HTTP_200_OK)

class ExitQueue(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logger = logging.getLogger(__name__)
        data = request.data
        user_id = data.get("userId")
        game_server = GameServerModel.objects.get(Q(firstPlayerId=user_id) | Q(secondPlayerId=user_id))
        try:
            waiting_player = WaitingPlayerModel.objects.get(player_id=user_id)
            waiting_player.delete()
        except WaitingPlayerModel.DoesNotExist:
            pass
        if game_server:
            if int(game_server.firstPlayerId) == int(user_id):
                game_server.firstPlayerId = -1
            if int(game_server.secondPlayerId) == int(user_id):
                game_server.secondPlayerId = -1
            game_server.state = 'waiting'
            game_server.save()
        return Response({"message": 'You left the queue'}, status=status.HTTP_200_OK)

        
#to check if properly connected
class UserDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Get the currently authenticated user

        # Assuming the user has a 'nickname' field in the profile model
        nickname = user.profile.nickname if hasattr(user, 'profile') else None

        # Return the user details
        return Response({
            'username': user.username,
            'email': user.email,
            'nickname': nickname,
            # Note: Never send the hashed password to the frontend!
        })