from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, RequestOTPSerializer, VerifyOTPSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if not User.objects.filter(email=email).exists():
                User.objects.create(email=email)
                return Response({'message': 'Registration successful. Please verify your email.'}, status=status.HTTP_201_CREATED)
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RequestOTPView(APIView):
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                user.generate_otp()
                # Send OTP via email
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {user.otp}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({'message': 'OTP sent to your email.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                if user.is_otp_valid(otp):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': 'Login successful.',
                        'token': str(refresh.access_token)
                    }, status=status.HTTP_200_OK)
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
