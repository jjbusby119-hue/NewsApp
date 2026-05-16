from rest_framework import serializers
from .models import Article, Newsletter, CustomUser, Publisher


class PublisherSerializer(serializers.ModelSerializer):
    """Lightweight publisher representation used inside other serializers."""
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'editors', 'journalists']


class JournalistSerializer(serializers.ModelSerializer):
    """Lightweight journalist representation used inside other serializers."""
    class Meta:
        model = CustomUser
        fields = ['id', 'username']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser with nested subscriptions."""
    subscriptions_to_publishers = PublisherSerializer(many=True, read_only=True)
    subscriptions_to_journalists = JournalistSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'role',
            'date_joined',
            'is_staff',
            'is_active',
        ]
        read_only_fields = ['id', 'role']


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article with nested journalist authors."""
    author = serializers.StringRelatedField(many=True, read_only=True)
    publisher = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'author',
            'published_at',
            'approved',
            'publisher',
        ]
        read_only_fields = ['id', 'author', 'published_at', 'approved',]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for Newsletter with nested journalist authors."""
    author = JournalistSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            'id',
            'title',
            'articles',
            'author',
            'created_at',
            'description',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'description',]
