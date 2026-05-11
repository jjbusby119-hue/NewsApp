from django.urls import path
from . import views


urlpatterns = [
    # Authentication URLs
    path('', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Article URLs
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('article/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('article/write/', views.ArticleCreateView.as_view(), name='article_write'),
    path('article/<int:pk>/write/', views.ArticleUpdateView.as_view(), name='article_write'),
    path('article/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('article/<int:pk>/approve/', views.approve_article, name='article_approve'),

    # Publisher URLs
    path('publisher/create/', views.PublisherCreateView.as_view(), name='publisher-create'),

    # Newsletter URLs
    path('newsletters/', views.NewsletterListView.as_view(), name='newsletter-list'),
    path('newsletter/<int:pk>/', views.NewsletterDetailView.as_view(), name='newsletter-detail'),
    path('newsletter/create/', views.NewsletterCreateView.as_view(), name='newsletter_form'),
    path('newsletter/<int:pk>/update/', views.NewsletterUpdateView.as_view(), name='newsletter_form'),
    path('newsletter/<int:pk>/delete/', views.NewsletterDeleteView.as_view(), name='newsletter_delete'),
    
    # Reader Subscription URLs
    path('subscriptions/', views.reader_subscriptions, name='reader-subscriptions'),
    path('subscribe/publisher/<int:publisher_id>/', views.subscribe_to_publisher, name='subscribe-publisher'),
    path('unsubscribe/publisher/<int:publisher_id>/', views.unsubscribe_from_publisher, name='unsubscribe-publisher'),
    path('subscribe/journalist/<int:journalist_id>/', views.subscribe_to_journalist, name='subscribe-journalist'),
    path('unsubscribe/journalist/<int:journalist_id>/', views.unsubscribe_from_journalist, name='unsubscribe-journalist'),

    # Auth
    path('api/token/', views.APILoginView.as_view(), name='api-token'),
    path('api/login/', views.APILoginView.as_view(), name='api-login'),
    path('api/logout/', views.APILogoutView.as_view(), name='api-logout'),

    # Articles — order matters: subscribed before <id>
    path('api/articles/', views.ArticleListCreateAPIView.as_view(), name='api-article-list'),
    path('api/articles/subscribed/', views.SubscribedArticlesAPIView.as_view(), name='api-article-subscribed'),
    path('api/articles/<int:pk>/', views.ArticleDetailAPIView.as_view(), name='api-article-detail'),
    path('api/articles/<int:pk>/approve/', views.ArticleApproveAPIView.as_view(), name='api-article-approve'),
]
