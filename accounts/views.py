from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from .models import User, PasswordResetToken
from .serializers import (
    SignupSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, UserSerializer
)
from .utils import send_welcome_email, send_reset_email
from server.utils import api_response


def _first_error_message(serializer):
    return list(serializer.errors.values())[0][0]


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = request.META.get('HTTP_AUTHORIZATION', '').strip()
        raw = raw.strip('"')
        print("RAW HEADER:", raw)
        if not raw:
            return None

        try:
            if raw.startswith('Bearer '):
                token_string = raw[len('Bearer '):].strip()
            elif raw.startswith('Token '):
                token_string = raw[len('Token '):].strip()
            else:
                token_string = raw

            print("TOKEN STRING:", token_string[:20])
            token_string = token_string.strip('"')
            validated = AccessToken(token_string)
            print("VALIDATED USER ID:", validated['user_id'])
            user_id = validated['user_id']
            user = User.objects.get(id=int(user_id))
            print("USER FOUND:", user.email)
            return (user, validated)
        except User.DoesNotExist:
            print("USER NOT FOUND")
            raise AuthenticationFailed('User not found.')
        except (TokenError, Exception) as e:
            print("TOKEN ERROR:", str(e))
            raise AuthenticationFailed('Invalid or expired token.')


# CORRECT ✅
class UpdateProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False)
    father_name = serializers.CharField(required=False)
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['full_name', 'age', 'father_name', 'profile_image']

        
class SignupView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(request_body=SignupSerializer)
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response("error", _first_error_message(serializer), http_status=400)

        user = serializer.save()
        send_welcome_email(user.email, user.full_name)
        return api_response("success", "Account created successfully.", UserSerializer(user).data, 201)


class LoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser, MultiPartParser]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response("error", _first_error_message(serializer), http_status=400)

        user = authenticate(email=serializer.validated_data['email'],
                            password=serializer.validated_data['password'])
        if not user:
            return api_response("error", "Invalid email or password.", http_status=401)

        refresh = RefreshToken.for_user(user)
        return api_response("success", "Login successful.", {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser, MultiPartParser]

    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response("error", _first_error_message(serializer), http_status=400)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return api_response("error", "No account found with this email.", http_status=404)

        token = PasswordResetToken.objects.create(user=user)
        send_reset_email(user.email, str(token.token))
        return api_response("success", "Password reset token sent to your email.")


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser, MultiPartParser]

    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response("error", _first_error_message(serializer), http_status=400)

        try:
            reset = PasswordResetToken.objects.get(
                token=serializer.validated_data['token'], is_used=False
            )
        except PasswordResetToken.DoesNotExist:
            return api_response("error", "Invalid or expired token.", http_status=400)

        reset.user.set_password(serializer.validated_data['new_password'])
        reset.user.save()
        reset.is_used = True
        reset.save()
        return api_response("success", "Password reset successfully.")


class GetProfileView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response("success", "Profile fetched successfully.", UserSerializer(request.user).data)


class UpdateProfileView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(request_body=UpdateProfileSerializer)
    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response("error", _first_error_message(serializer), http_status=400)

        updated_user = serializer.save()
        return api_response("success", "Profile updated successfully.", UserSerializer(updated_user).data)