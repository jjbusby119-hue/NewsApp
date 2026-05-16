from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView
from django.views import View
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.db.models import Q
from .models import Article, Newsletter, CustomUser, Publisher
from .forms import ArticleForm, ArticleApprovalForm, NewsletterForm
from .forms import CustomUserCreationForm, CustomLoginForm, UserProfileForm
from .serializers import ArticleSerializer, UserSerializer, NewsletterSerializer, PublisherSerializer


# Utility functions for access control
def is_reader(user):
    """Return 'True' if user is authenticated and has role 'Reader'"""
    return user.is_authenticated and user.role == 'Reader'


def is_editor(user):
    """Return ``True`` if *user* is authenticated with the Editor role."""
    return user.is_authenticated and user.role == 'Editor'


def is_journalist(user):
    """Return ``True`` if *user* is authenticated with the Journalist role."""
    return user.is_authenticated and user.role == 'Journalist'


def can_view_content(user):
    """Return ``True`` if *user* holds any content-viewing role (Reader, Editor, Journalist)."""
    return user.is_authenticated and user.role in ['Reader', 'Editor', 'Journalist']


def can_create_content(user):
    """Return ``True`` if *user* may create content (Journalist only)."""
    return user.is_authenticated and user.role in ['Journalist']
 

def can_edit_content(user):
    """Return ``True`` if *user* may edit content (Editor or Journalist)."""
    return user.is_authenticated and user.role in ['Editor', 'Journalist']
 

def can_delete_content(user):
    """Return ``True`` if *user* may delete content (Editor or Journalist)."""
    return user.is_authenticated and user.role in ['Editor', 'Journalist']
 

def can_approve_articles(user):
    """Return ``True`` if *user* may approve articles (Editor only)."""
    return user.is_authenticated and user.role in ['Editor']


# Login, Logout, Profile and Signup Views
class SignupView(CreateView):
    """Register a new user and redirect to login on success."""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Save the user
        response = super().form_valid(form)
        
        # Assign default role as Reader if not specified
        if not self.object.role:
            self.object.role = 'Reader'
            self.object.save()
        
        messages.success(self.request, 'Account created successfully! Please login.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in.')
            return redirect('article-list')
        return super().dispatch(request, *args, **kwargs)


class LoginView(FormView):
    """Authenticate a user and redirect to the article list."""
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('article-list')
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Welcome back, {user.username}!')
            
            # Redirect based on role if needed
            if user.role == 'Editor':
                messages.info(self.request, 'You have editor privileges.')
            elif user.role == 'Journalist':
                messages.info(self.request, 'You can create and manage your content.')
            
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('article-list')
        return super().dispatch(request, *args, **kwargs)


class LogoutView(View):
    """Log out the current user and redirect to login."""
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')


@login_required
def profile_view(request):
    """Display the current user's profile.
 
    :param request: The HTTP request.
    :returns: Rendered profile, or redirects to article write.
    """

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'registration/profile.html', {'form': form})


# Article Views
class ArticleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List articles filtered by the current user's role."""
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    
    def test_func(self):
        return can_view_content(self.request.user)


    def get_queryset(self):
        queryset = Article.objects.all()
        # Readers can only see approved articles
        if self.request.user.role == 'Reader':
            queryset = queryset.filter(approved=True)
        # Journalists can see their own articles and approved articles
        elif self.request.user.role == 'Journalist':
            queryset = queryset.filter(
                models.Q(approved=True) | models.Q(author=self.request.user)
            )
        # Editors can see all articles
        return queryset


class ArticleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Display a single article, enforcing role-based visibility."""
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def test_func(self):
        article = self.get_object()
        user = self.request.user
        
        # Readers can only view approved articles
        if user.role == 'Reader':
            return article.approved
        # Journalists can view their own articles or approved ones
        elif user.role == 'Journalist':
            return article.approved or user == article.author
        # Editors can view all articles
        return can_view_content(user)


class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new article (Journalists only)."""
    model = Article
    form_class = ArticleForm  # Use custom form instead of 'fields'
    template_name = 'articles/article_write.html'
    success_url = reverse_lazy('article-list')
    
    def test_func(self):
        return can_create_content(self.request.user)
    
    def form_valid(self, form):
        form.instance.published_at = timezone.now()
        form.instance.author = self.request.user
        
        response = super().form_valid(form)
        
        messages.success(self.request, 'Article created successfully!')
        return response


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing article. Journalists may only edit their own."""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_write.html'

    def test_func(self):
        article = self.get_object()
        user = self.request.user
        
        # Journalists can only edit their own articles
        if user.role == 'Journalist':
            return user == article.author
        # Editors can edit any article
        return can_edit_content(user)
    
    def get_success_url(self):
        return reverse_lazy('article-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Article updated successfully!')
        return super().form_valid(form)


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an article. Journalists may only delete their own."""
    model = Article
    template_name = 'articles/article_delete.html'
    success_url = reverse_lazy('article-list')

    def test_func(self):
        article = self.get_object()
        user = self.request.user
        
        # Journalists can only delete their own articles
        if user.role == 'Journalist':
            return user == article.author
        # Editors can delete any article
        return can_delete_content(user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Article deleted successfully!')
        return super().delete(request, *args, **kwargs)
    

class PublisherCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new publisher (Journalists only)."""
    model = Publisher
    fields = ['name']
    template_name = 'publishers/publisher_form.html'
    success_url = reverse_lazy('article_write')

    def test_func(self):
        return self.request.user.role == 'Journalist'

    def form_valid(self, form):
        messages.success(self.request, 'Publisher created successfully!')
        return super().form_valid(form)


# SINGLE CONSOLIDATED APPROVAL FUNCTION
@login_required
@user_passes_test(can_approve_articles)
def approve_article(request, pk):
    """Approve an article for publishing and notify the author by email.
 
    :param request: The HTTP request (must be POST to approve).
    :param pk: Primary key of the :class:`Article` to approve.
    :returns: Redirect to the article detail page on success, or the approval form.
    """

    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        form = ArticleApprovalForm(request.POST, instance=article)
        if form.is_valid():
            # Save the form (which sets approved=True)
            form.save()
            
            # Get feedback from the form
            feedback = form.cleaned_data.get('feedback', '')
            
            # Handle post-approval logic (without signals)
            try:
                # Send email notification to the article author
                subject = f'Article Approved: {article.title}'
                message = f"""
                Your article "{article.title}" has been approved and published.
                
                Article Details:
                - Title: {article.title}
                - Published Date: {article.published_at}
                - Approved by: {request.user.username}
                """
                
                # Add feedback to email if provided
                if feedback:
                    message += f"\n\nEditor Feedback:\n{feedback}"
                
                message += f"\n\nYou can view your published article at: {request.build_absolute_uri(f'/article/{article.pk}/')}"
                
                # If author is a registered user, send email
                try:
                    author_user = article.author
                    if author_user.email:
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [author_user.email],
                            fail_silently=True,
                        )
                except CustomUser.DoesNotExist:
                    # If author is not a registered user, log or handle accordingly
                    pass
                
                # Post notification to admin
                if hasattr(settings, 'ADMIN_NOTIFICATION_EMAIL'):
                    admin_message = f"""
                    Article "{article.title}" has been approved by {request.user.username}.
                    Article ID: {article.id}
                    Approval Date: {timezone.now()}
                    """
                    
                    if feedback:
                        admin_message += f"\n\nEditor Feedback:\n{feedback}"
                    
                    send_mail(
                        'New Article Approved',
                        admin_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_NOTIFICATION_EMAIL],
                        fail_silently=True,
                    )
                
                messages.success(request, f'Article "{article.title}" has been approved and published!')
                
            except Exception as e:
                messages.error(request, f'Article approved but notification failed: {str(e)}')
            
            return redirect('article-detail', pk=article.pk)
    else:
        form = ArticleApprovalForm(instance=article)
    
    return render(request, 'articles/article_approve.html', {
        'form': form,
        'article': article
    })


# Newsletter Views
class NewsletterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all newsletters. Accessible to all authenticated roles."""
    model = Newsletter
    template_name = 'newsletters/newsletter_list.html'
    context_object_name = 'newsletters'
    
    def test_func(self):
        return can_view_content(self.request.user)
    
    def get_queryset(self):
        queryset = Newsletter.objects.all()
        # Readers can view all newsletters
        if self.request.user.role == 'Reader':
            return queryset
        # Journalists can see their own newsletters and all others
        elif self.request.user.role == 'Journalist':
            return queryset
        # Editors can see all newsletters
        return queryset


class NewsletterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Display a single newsletter."""
    model = Newsletter
    template_name = 'newsletters/newsletter_detail.html'
    context_object_name = 'newsletter'

    def test_func(self):
        return can_view_content(self.request.user)


class NewsletterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a newsletter and associate it with the author (Journalists only)."""
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletters/newsletter_form.html'
    success_url = reverse_lazy('newsletter-list')
    
    def test_func(self):
        return can_create_content(self.request.user)
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        response = super().form_valid(form)
        
        # If user is a Journalist, add to their published newsletters
        if self.request.user.role == 'Journalist':
            self.request.user.published_newsletters.add(self.object)
        
        messages.success(self.request, 'Newsletter created successfully!')
        return response


class NewsletterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a newsletter. Journalists may only edit their own.""" 
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletters/newsletter_form.html'
    
    def test_func(self):
        newsletter = self.get_object()
        user = self.request.user
        
        # Journalists can only edit their own newsletters
        if user.role == 'Journalist':
            return user in newsletter.author.all()
        # Editors can edit any newsletter
        return can_edit_content(user)
    
    def get_success_url(self):
        return reverse_lazy('newsletter-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Newsletter updated successfully!')
        return super().form_valid(form)


class NewsletterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a newsletter. Journalists may only delete their own."""
    model = Newsletter
    template_name = 'newsletters/newsletter_delete.html'
    success_url = reverse_lazy('newsletter-list')

    def test_func(self):
        newsletter = self.get_object()
        user = self.request.user
        
        # Journalists can only delete their own newsletters
        if user.role == 'Journalist':
            return user in newsletter.author.all()
        # Editors can delete any newsletter
        return can_delete_content(user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Newsletter deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Reader-specific views
@login_required
def reader_subscriptions(request):
    """Display the current user's subscribed publishers and journalists.
 
    :param request: The HTTP request.
    :returns: Rendered subscriptions page.
    """

    user = request.user
    subscribed_publishers = user.subscriptions_to_publishers.all()
    subscribed_journalists = user.subscriptions_to_journalists.all()
    
    context = {
        'subscribed_publishers': subscribed_publishers,
        'subscribed_journalists': subscribed_journalists,
    }
    
    return render(request, 'readers/subscriptions.html', context)


@login_required
def subscribe_to_publisher(request, publisher_id):
    """Subscribe the current user to a publisher.
 
    :param publisher_id: PK of the :class:`Publisher` to subscribe to.
    """

    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscriptions_to_publishers.add(publisher)
    messages.success(request, f'Subscribed to {publisher.name} successfully!')
    return redirect('reader-subscriptions')


@login_required
def unsubscribe_from_publisher(request, publisher_id):
    """Unsubscribe the current user from a publisher.
 
    :param publisher_id: PK of the :class:`Publisher` to unsubscribe from.
    """
     
    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscriptions_to_publishers.remove(publisher)
    messages.success(request, f'Unsubscribed from {publisher.name} successfully!')
    return redirect('reader-subscriptions')


@login_required
def subscribe_to_journalist(request, journalist_id):
    """Subscribe the current user to a journalist.
 
    :param journalist_id: PK of the journalist (:class:`CustomUser`) to subscribe to.
    """

    journalist = get_object_or_404(
    CustomUser,
    id=journalist_id,
    role='Journalist'
    )
    request.user.subscriptions_to_journalists.add(journalist)
    messages.success(request, f'Subscribed to {journalist.username} successfully!')
    return redirect('reader-subscriptions')


@login_required
def unsubscribe_from_journalist(request, journalist_id):
    """Allow readers to unsubscribe from a journalist.
 
    :param journalist_id: PK of the journalist (:class:`CustomUser`) to unsubscribe from.
    """

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role='Journalist'
    )
    request.user.subscriptions_to_journalists.remove(journalist)
    messages.success(request, f'Unsubscribed from {journalist.username} successfully!')
    return redirect('reader-subscriptions')


# DRF Permission Classes
class IsJournalist(permissions.BasePermission):
    """Allow access to Journalists only."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Journalist'


class IsEditorOrJournalist(permissions.BasePermission):
    """Allow Editors full access; restrict Journalists to their own objects."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Editor', 'Journalist']

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'Editor':
            return True
        # Journalists may only touch their own articles
        return obj.author == request.user


class IsEditor(permissions.BasePermission):
    """Allow access to Editors only."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Editor'


class IsAuthenticatedReader(permissions.BasePermission):
    """Allow access to any authenticated user."""
    def has_permission(self, request, view):
        return request.user.is_authenticated


# Authentication Endpoint
class APILoginView(ObtainAuthToken):
    """Return an auth token and basic user info on successful login.
 
    :returns: JSON with ``token``, ``user_id``, ``username``, and ``role``.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'role': user.role,
        })


class APILogoutView(APIView):
    """Delete the current user's auth token, effectively logging them out."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


# Article API Views
class ArticleListCreateAPIView(APIView):
    """
    List articles or create a new one.
 
    - ``GET``  — Returns articles filtered by the caller's role.
    - ``POST`` — Creates an article; Journalists only.
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsJournalist()]
        return [IsAuthenticatedReader()]

    def get(self, request):
        user = request.user
        if user.role == 'Editor':
            articles = Article.objects.all()
        elif user.role == 'Journalist':
            articles = Article.objects.filter(
                Q(approved=True) | Q(author=user)
            ).distinct()
        else:
            # Readers see only approved articles
            articles = Article.objects.filter(approved=True)

        serializer = ArticleSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ArticleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            article = serializer.save(
                author=request.user,
                published_at=timezone.now()
            )
            article.author.add(request.user)
            return Response(ArticleSerializer(article).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleDetailAPIView(APIView):
    """
    Retrieve, update, or delete a single article.
 
    - ``GET``    — Visible per role (Readers: approved only).
    - ``PUT``    — Editors or the article's own Journalist.
    - ``DELETE`` — Editors or the article's own Journalist.
    """

    def _get_article(self, pk):
        return get_object_or_404(Article, pk=pk)

    def _can_view(self, user, article):
        if user.role == 'Editor':
            return True
        if user.role == 'Journalist':
            return article.approved or article.author == user
        return article.approved  # Reader

    def _can_modify(self, user, article):
        if user.role == 'Editor':
            return True
        if user.role == 'Journalist':
            return user == article.author
        return False

    def get(self, request, pk):
        article = self._get_article(pk)
        if not self._can_view(request.user, article):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ArticleSerializer(article, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        if request.user.role not in ['Editor', 'Journalist']:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        article = self._get_article(pk)
        if not self._can_modify(request.user, article):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ArticleSerializer(
            article, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.role not in ['Editor', 'Journalist']:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        article = self._get_article(pk)
        if not self._can_modify(request.user, article):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribedArticlesAPIView(APIView):
    """Return approved articles from the user's subscribed publishers and journalists."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        subscribed_publishers = user.subscriptions_to_publishers.all()
        subscribed_journalists = user.subscriptions_to_journalists.all()

        articles = Article.objects.filter(
            Q(publisher__in=subscribed_publishers) |
            Q(author__in=subscribed_journalists),
            approved=True
        ).distinct()

        serializer = ArticleSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)


class ArticleApproveAPIView(APIView):
    """Approve an article (Editors only).
 
    :param pk: Primary key of the :class:`Article` to approve.
    :returns: Serialized article data with HTTP 200.
    """
    
    permission_classes = [IsEditor]

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        article.approved = True
        article.save()
        return Response(
            ArticleSerializer(article, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
