from django.shortcuts import render
from rest_framework import generics
from .models import CustomUser
from .serializers import * 
from .models import CustomUser, UserProfile, GuideProfile
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsGuideUser
from django.db.models import Count, Avg, Sum
from django.utils.timezone import now
from django.db.models.functions import ExtractMonth, ExtractWeek
from django.conf import settings
from .langchain_rag import LangChainRAG  
from .langchain_sql import LangChainSQL

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer

class GuideRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = GuideRegistrationSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type == 'User':
            profile = UserProfile.objects.get(user=user)
            profile_serializer = UserProfileSerializer(profile)
        elif user.user_type == 'Guide':
            profile = GuideProfile.objects.get(user=user)
            profile_serializer = GuideProfileSerializer(profile)
        else:
            return Response({"error": "Invalid user type"}, status=400)

        user_serializer = CustomUserSerializer(user)
        user_data = user_serializer.data
        user_data['profile'] = profile_serializer.data

        return Response(user_data)
    
class GuideListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        guides = CustomUser.objects.filter(user_type='Guide')
        serializer = GuideSerializer(guides, many=True)
        return Response(serializer.data)

class ReservationListByUserView(generics.ListAPIView):
    serializer_class = ReservationSerializerList
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.filter(user=user)

class CreateReservationView(generics.CreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GuideRatingListView(generics.ListAPIView):
    serializer_class = RatingSerializerList
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Rating.objects.filter(user=user)

class GuideReservationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsGuideUser]
    serializer_class = ReservationSerializerList

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.filter(guide=user)
    
class ChangeReservationStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsGuideUser]
    queryset = Reservation.objects.all()
    serializer_class = ReservationStatusSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        reservation = self.get_object()

        status_to_change = request.data.get('status')
        if status_to_change not in dict(Reservation.STATUS_CHOICES).keys():
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        reservation.status = status_to_change
        reservation.save()
        return Response({"detail": "Reservation status updated successfully."}, status=status.HTTP_200_OK)
    
class RatingsListByGuideView(generics.ListAPIView):
    serializer_class = RatingSerializerList
    permission_classes = [IsAuthenticated, IsGuideUser]

    def get_queryset(self):
        return Rating.objects.filter(guide=self.request.user)


class GuideStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsGuideUser]

    def get(self, request):
        guide = request.user

        # Total number of reservations
        total_reservations = Reservation.objects.filter(guide=guide).count()

        # Number of reservations by status
        reservations_by_status = Reservation.objects.filter(guide=guide).values('status').annotate(count=Count('status'))

        # Number of reservations per month
        current_year = now().year
        reservations_per_month = Reservation.objects.filter(
            guide=guide,
            start_date__year=current_year
        ).annotate(month=ExtractMonth('start_date')).values('month').annotate(count=Count('id')).order_by('month')

        # Number of reservations per week
        reservations_per_week = Reservation.objects.filter(
            guide=guide,
            start_date__year=current_year
        ).annotate(week=ExtractWeek('start_date')).values('week').annotate(count=Count('id')).order_by('week')

        # Total number of unique users
        unique_users = Reservation.objects.filter(guide=guide).values('user').distinct().count()

        # Average rating
        average_rating = Rating.objects.filter(guide=guide).aggregate(avg_rating=Avg('rating'))['avg_rating']

        # Total number of ratings
        total_ratings = Rating.objects.filter(guide=guide).count()

        # Total revenue
        total_revenue = Reservation.objects.filter(guide=guide, status='Completed').aggregate(total=Sum('price'))['total']

        # Most common users
        most_common_users = Reservation.objects.filter(guide=guide).values('user__first_name', 'user__last_name').annotate(count=Count('user')).order_by('-count')[:5]

        # Average group size
        average_group_size = Reservation.objects.filter(guide=guide).aggregate(avg_group_size=Avg('number_of_people'))['avg_group_size']

        # Repeat users
        repeat_users = Reservation.objects.filter(guide=guide).values('user').annotate(count=Count('user')).filter(count__gt=1).count()

        data = {
            'total_reservations': total_reservations,
            'reservations_by_status': list(reservations_by_status),
            'reservations_per_month': list(reservations_per_month),
            'reservations_per_week': list(reservations_per_week),
            'unique_users': unique_users,
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'total_revenue': total_revenue,
            'most_common_users': list(most_common_users),
            'average_group_size': average_group_size,
            'repeat_users': repeat_users,
            # Add more stats here as needed
        }

        return Response(data)


class CustomDatabaseSettingsView(APIView):
    def get(self, request):
        database_settings = settings.DATABASES
        return Response(database_settings, status=status.HTTP_200_OK)


class RAGView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rag_model = LangChainRAG()

    def post(self, request):
        # Spróbuj odczytać dane jako JSON
        try:
            input_text = request.data.get("input", "")
        except Exception as e:
            return Response({"error": f"Invalid JSON data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not input_text:
            return Response({"error": "Input is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            answer = self.rag_model.get_answer(input_text)
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SQLView(APIView):
    permission_classes = [IsAuthenticated, IsGuideUser]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sql_model = LangChainSQL()

    def post(self, request):
        try:
            input_text = request.data.get("input", "")
        except Exception as e:
            return Response({"error": f"Invalid JSON data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not input_text:
            return Response({"error": "Input is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self.sql_model.get_answer(input_text)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)