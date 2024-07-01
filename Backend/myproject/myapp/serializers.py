from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['city']

class GuideProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideProfile
        fields = ['language', 'bio']

class UserRegistrationSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'phone', 'userprofile']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('userprofile')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            user_type='User'
        )
        UserProfile.objects.create(user=user, **profile_data)
        return user

class GuideRegistrationSerializer(serializers.ModelSerializer):
    guideprofile = GuideProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'phone', 'guideprofile']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('guideprofile')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            user_type='Guide'
        )
        GuideProfile.objects.create(user=user, **profile_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['user_type'] = user.user_type

        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user_type to the response data
        data['user_type'] = self.user.user_type

        return data
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone', 'user_type']


class GuideSerializer(serializers.ModelSerializer):
    guideprofile = GuideProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'guideprofile']


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'guide', 'start_date', 'end_date', 'number_of_people', 'additional_info' ]

    def create(self, validated_data):
        # Calculate price based on number_of_people
        validated_data['price'] = validated_data['number_of_people'] * 200
        return super().create(validated_data)
    
class ReservationSerializerList(serializers.ModelSerializer):
    guide_first_name = serializers.CharField(source='guide.first_name', read_only=True)
    guide_last_name = serializers.CharField(source='guide.last_name', read_only=True)

    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)

    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'user','user_first_name' ,'user_last_name','user_email','guide', 'guide_first_name', 'guide_last_name', 'start_date', 'end_date', 'number_of_people', 'additional_info', 'price','status']

    def get_guide_first_name(self, obj):
        return obj.guide.first_name

    def get_guide_last_name(self, obj):
        return obj.guide.last_name

class RatingSerializer(serializers.ModelSerializer):
    guide = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(user_type='Guide')
    )
    class Meta:
        model = Rating
        fields = ['id', 'guide', 'description', 'rating', 'is_public']

class RatingSerializerList(serializers.ModelSerializer):
    guide_first_name = serializers.CharField(source='guide.first_name', read_only=True)
    guide_last_name = serializers.CharField(source='guide.last_name', read_only=True)

    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Rating
        fields = ['id','user_first_name' ,'user_last_name','guide_first_name', 'guide_last_name', 'description', 'rating']


class ReservationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['status']

    
