from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from .models import User, PasswordResetToken
from .serializers import (
    SignupSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, UserSerializer
)
from .utils import api_response, send_welcome_email, send_reset_email


def _first_error_message(serializer):
    return list(serializer.errors.values())[0][0]


class SignupView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

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
    parser_classes = [FormParser]

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
    parser_classes = [FormParser]

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
    parser_classes = [FormParser]

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