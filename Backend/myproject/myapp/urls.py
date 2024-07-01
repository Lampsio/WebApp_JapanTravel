from django.urls import path
from .views import *

urlpatterns = [
    path('register/user/', UserRegistrationView.as_view(), name='register_user'),
    path('register/guide/', GuideRegistrationView.as_view(), name='register_guide'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('guide-list/', GuideListView.as_view(), name='guide-list'),
    path('reservation-list-by-user/', ReservationListByUserView.as_view(), name='reservation-list-by-user'),
    path('create-reservation/', CreateReservationView.as_view(), name='create-reservation'),
    path('create-ratings/', RatingListCreateView.as_view(), name='rating-list-create'),
    path('guide-ratings/', GuideRatingListView.as_view(), name='guide-rating-list'),
    path('guide/ratings/', RatingsListByGuideView.as_view(), name='guide-ratings'),
    path('guide/reservations/', GuideReservationsView.as_view(), name='guide-reservations'),
    path('guide/reservation/<int:pk>/status/', ChangeReservationStatusView.as_view(), name='change-reservation-status'),
    path('guide/statistics/', GuideStatisticsView.as_view(), name='guide_statistics'),
    path('custom-settings/', CustomDatabaseSettingsView.as_view(), name='custom-settings'),
    path('rag/', RAGView.as_view(), name='rag_api'),
    path('sql/', SQLView.as_view(), name='sql_api'),
]
