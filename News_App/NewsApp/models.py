from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='articles'
    )
    publisher = models.ForeignKey(
        'Publisher',
        on_delete=models.CASCADE,
        related_name='articles',
        blank=True,
        null=True
    )
    approved = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    content = models.TextField()
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.title
    
    class Meta:
        permissions = [
            ("can_view_article", "Can view article"),
            ("can_create_article", "Can create article"),
            ("can_update_article", "Can update article"),
            ("can_delete_article", "Can delete article"),
        ]


class Publisher(models.Model):
    name = models.CharField(max_length=100)
    editors = models.ManyToManyField(
        'CustomUser',
        related_name='editor_publishers',
        blank=True
    )
    journalists = models.ManyToManyField(
        'CustomUser',
        related_name='journalist_publishers',
        blank=True
    )
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.name


class Newsletter(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    author = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='newsletters')
    created_at = models.DateTimeField(auto_now_add=True)
    articles = models.ManyToManyField('Article')
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.title
    
    class Meta:
        permissions = [
            ("can_view_newsletter", "Can view newsletter"),
            ("can_create_newsletter", "Can create newsletter"),
            ("can_update_newsletter", "Can update newsletter"),
            ("can_delete_newsletter", "Can delete newsletter"),
        ]

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('Editor', 'Editor'),
        ('Journalist', 'Journalist'),
        ('Reader', 'Reader'),
    ]

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Reader')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    id = models.AutoField(primary_key=True)

# Reader-specific fields
    subscriptions_to_publishers = models.ManyToManyField(
        'Publisher',
        related_name='subscribed_readers',
        blank=True
    )
    subscriptions_to_journalists = models.ManyToManyField(
        'CustomUser',
        related_name='journalist_subscribers',
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if not is_new:
            if self.role == 'Journalist':
                self.subscriptions_to_publishers.clear()
                self.subscriptions_to_journalists.clear()

        self.assign_group()

    def assign_group(self):
        """Assign user to appropriate group based on role and set permissions"""
        from django.contrib.auth.models import Group, Permission
        
        # Get or create groups
        reader_group, _ = Group.objects.get_or_create(name='Reader')
        editor_group, _ = Group.objects.get_or_create(name='Editor')
        journalist_group, _ = Group.objects.get_or_create(name='Journalist')
        
        # Remove user from all groups first
        self.groups.clear()
        
        # Assign permissions based on role
        if self.role == 'Reader':
            self.groups.add(reader_group)
            reader_group.permissions.add(
                Permission.objects.get(codename='can_view_article'),
                Permission.objects.get(codename='can_view_newsletter'),
            )
            
        elif self.role == 'Editor':
            self.groups.add(editor_group)
            editor_group.permissions.add(
                Permission.objects.get(codename='can_view_article'),
                Permission.objects.get(codename='can_update_article'),
                Permission.objects.get(codename='can_delete_article'),
                Permission.objects.get(codename='can_view_newsletter'),
                Permission.objects.get(codename='can_update_newsletter'),
                Permission.objects.get(codename='can_delete_newsletter'),
            )
            
        elif self.role == 'Journalist':
            self.groups.add(journalist_group)
            journalist_group.permissions.add(
                Permission.objects.get(codename='can_create_article'),
                Permission.objects.get(codename='can_view_article'),
                Permission.objects.get(codename='can_update_article'),
                Permission.objects.get(codename='can_delete_article'),
                Permission.objects.get(codename='can_create_newsletter'),
                Permission.objects.get(codename='can_view_newsletter'),
                Permission.objects.get(codename='can_update_newsletter'),
                Permission.objects.get(codename='can_delete_newsletter'),
            )
