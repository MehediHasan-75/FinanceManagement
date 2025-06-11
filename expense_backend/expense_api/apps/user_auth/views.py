from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate

from .authentication import IsAuthenticatedCustom, decode_refresh_token, generate_access_token, generate_refresh_token
from .permission import JWTAuthentication
from .serializers import UserSerializer, userRegisterSerializer
from django.contrib.auth.models import User

# Create your views here.

class UserRegisterView(APIView):
    def post(self, request):
        serializer = userRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            response = Response({
                'message': "User registered successfully.",
                'user': UserSerializer(user).data,
                'access_token': access_token,
                'refresh_token': refresh_token
            })

            # response.set_cookie('refresh_token', refresh_token, httponly=True)
            # response.set_cookie('access_token', access_token, httponly=True)
            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=True, path='/', samesite='Lax',
                secure=False, max_age=7*24*60*60  # <-- Important
            )
            response.set_cookie(
                'access_token', access_token,
                httponly=True, path='/', samesite='Lax',
                secure=False, max_age=60*60  # <-- 15 minutes
            )
            
            return response

        return Response(serializer.errors, status=400)
    
    
class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request, *args, **kwargs):
        try:
            data = User.objects.all()
            serializer = UserSerializer(data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching user data.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class loginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            response =  Response({'message': "Login successful.",
                             'user': UserSerializer(user).data,
                                'access_token': generate_access_token(user),
                                'refresh_token': generate_refresh_token(user)
                             })
            # response.set_cookie('refresh_token', generate_refresh_token(user), httponly=True)
            # response.set_cookie('access_token', generate_access_token(user), httponly=True)
            response.set_cookie(
                'refresh_token', generate_refresh_token(user),
                httponly=True, path='/', samesite='Lax',
                secure=False, max_age=7*24*60*60  # <-- Important
            )
            response.set_cookie(
                'access_token', generate_access_token(user),
                httponly=True, path='/', samesite='Lax',
                secure=False, max_age=60*60  # <-- 15 minutes
            )
            return response
        return Response({'message': "Invalid credentials."})
    
class logoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]
    
    def post(self, request):
        print('logoutView')
        response = Response({'message': 'Logged out successfully'})
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]
    def get(self, request, *args, **kwargs):
        try:
            user_id = self.kwargs.get('user_id')
            queryset = User.objects.get(id=user_id)
            serializer = UserSerializer(queryset, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {
                    "error": "User Not Found", 
                    "details": str(e)
                },
                status=status.HTTP_404_NOT_FOUND
            )

class UpdateUserDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]
    
    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        newpassword = request.data.get('newpassword')
        newpassword2 = request.data.get('newpassword2')

        if newpassword != newpassword2:
            return Response({
                "message": "New passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Find the user
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"message": "User with this email not found"}, status=status.HTTP_404_NOT_FOUND)
        elif username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"message": "User with this username not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Username or email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Authenticate using actual username
        auth_user = authenticate(username=user.username, password=password)
        if not auth_user:
            return Response({"message": "Authentication failed"}, status=status.HTTP_401_UNAUTHORIZED)

        # Step 3: Update password
        user.set_password(newpassword)
        user.save()

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
    
    
class UdateAccessToken(APIView):
    authentication_classes = []  # No need for auth here — using refresh_token
    permission_classes = []

    def get(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'message': "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user_id = decode_refresh_token(refresh_token)
            user = User.objects.get(id=user_id)

            access_token = generate_access_token(user)
            response = Response({
                'message': "Access token update successful.",
                'user': UserSerializer(user).data,
                'access_token': access_token
            })

            response.set_cookie(
                'access_token', access_token,
                httponly=True, path='/', samesite='Lax',
                secure=False, max_age=60*60  # <-- 15 minutes
            )
            return response

        except User.DoesNotExist:
            return Response({'message': "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': "Invalid refresh token.", 'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "error": "Failed to retrieve user info",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )       
        