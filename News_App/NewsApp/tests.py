from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import Article, Newsletter, CustomUser, Journalist, Publisher


# Helpers
def make_user(username, role, password="pass1234"):
    user = CustomUser.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        role=role,
    )
    token, _ = Token.objects.get_or_create(user=user)
    return user, token


def auth_client(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def make_article(author_user, approved=False):
    article = Article.objects.create(
        title="Test Article",
        author=author_user.username,
        publisher="Default Publisher",
        approved=approved,
        published_at=timezone.now(),
        content="Some content.",
    )
    article.journalist_authors.add(author_user)
    return article


# 1. Authentication
class AuthenticationTests(TestCase):

    def setUp(self):
        self.user, self.token = make_user("journalist1", "Journalist")

    def test_login_success_returns_token_and_role(self):
        response = APIClient().post(reverse("api-login"), {
            "username": "journalist1", "password": "pass1234"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["role"], "Journalist")

    def test_login_wrong_credentials_returns_400(self):
        response = APIClient().post(reverse("api-login"), {
            "username": "journalist1", "password": "wrong"
        })
        self.assertEqual(response.status_code, 400)

    def test_logout_deletes_token(self):
        client = auth_client(self.token)
        client.post(reverse("api-logout"))
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_unauthenticated_request_returns_401(self):
        response = APIClient().get(reverse("api-article-list"))
        self.assertEqual(response.status_code, 401)


# 2. Article visibility per role
class ArticleVisibilityTests(TestCase):

    def setUp(self):
        self.journalist, self.journalist_token = make_user("j1", "Journalist")
        self.editor, self.editor_token = make_user("e1", "Editor")
        self.reader, self.reader_token = make_user("r1", "Reader")

        other_journalist, _ = make_user("j_other", "Journalist")
        self.approved = make_article(other_journalist, approved=True)
        self.own_unapproved = make_article(self.journalist, approved=False)
        self.other_unapproved = make_article(other_journalist, approved=False)

    def test_reader_sees_only_approved_articles(self):
        response = auth_client(self.reader_token).get(reverse("api-article-list"))
        ids = [a["id"] for a in response.data]
        self.assertIn(self.approved.id, ids)
        self.assertNotIn(self.own_unapproved.id, ids)
        self.assertNotIn(self.other_unapproved.id, ids)

    def test_journalist_sees_approved_and_own_unapproved(self):
        response = auth_client(self.journalist_token).get(reverse("api-article-list"))
        ids = [a["id"] for a in response.data]
        self.assertIn(self.approved.id, ids)
        self.assertIn(self.own_unapproved.id, ids)
        self.assertNotIn(self.other_unapproved.id, ids)

    def test_editor_sees_all_articles(self):
        response = auth_client(self.editor_token).get(reverse("api-article-list"))
        ids = [a["id"] for a in response.data]
        self.assertIn(self.approved.id, ids)
        self.assertIn(self.own_unapproved.id, ids)
        self.assertIn(self.other_unapproved.id, ids)


# 3. Article creation
class ArticleCreateTests(TestCase):

    def setUp(self):
        self.journalist, self.journalist_token = make_user("j_create", "Journalist")
        self.reader, self.reader_token = make_user("r_create", "Reader")
        self.editor, self.editor_token = make_user("e_create", "Editor")
        self.payload = {"title": "Breaking News", "content": "Important content."}

    def test_journalist_can_create_article_and_becomes_author(self):
        response = auth_client(self.journalist_token).post(
            reverse("api-article-list"), self.payload
        )
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(pk=response.data["id"])
        self.assertFalse(article.approved)
        self.assertIn(self.journalist, article.journalist_authors.all())

    def test_reader_cannot_create_article(self):
        response = auth_client(self.reader_token).post(
            reverse("api-article-list"), self.payload
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_create_article(self):
        response = auth_client(self.editor_token).post(
            reverse("api-article-list"), self.payload
        )
        self.assertEqual(response.status_code, 403)


# 4. Article approval and deletion
class ArticleApproveDeleteTests(TestCase):

    def setUp(self):
        self.editor, self.editor_token = make_user("ed1", "Editor")
        self.journalist, self.journalist_token = make_user("jo1", "Journalist")
        self.other_journalist, self.other_token = make_user("jo2", "Journalist")

        self.article = make_article(self.journalist, approved=False)

    def test_editor_can_approve_article(self):
        auth_client(self.editor_token).post(
            reverse("api-article-approve", kwargs={"pk": self.article.pk})
        )
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    def test_non_editor_cannot_approve_article(self):
        response = auth_client(self.journalist_token).post(
            reverse("api-article-approve", kwargs={"pk": self.article.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_delete_any_article(self):
        response = auth_client(self.editor_token).delete(
            reverse("api-article-detail", kwargs={"pk": self.article.pk})
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_journalist_cannot_delete_another_journalists_article(self):
        response = auth_client(self.other_token).delete(
            reverse("api-article-detail", kwargs={"pk": self.article.pk})
        )
        self.assertEqual(response.status_code, 403)


# 5. Subscribed articles feed
class SubscribedFeedTests(TestCase):

    def setUp(self):
        self.reader, self.reader_token = make_user("reader_sub", "Reader")
        self.journalist, _ = make_user("j_feed", "Journalist")

        self.subscribed_pub = Publisher.objects.create(name="SubPublisher")
        self.reader.subscriptions_to_publishers.add(self.subscribed_pub)

    def test_unapproved_articles_excluded_from_subscribed_feed(self):
        unapproved = Article.objects.create(
            title="Unapproved", author="j_feed", publisher=self.subscribed_pub.name,
            approved=False, published_at=timezone.now(), content="content",
        )
        response = auth_client(self.reader_token).get(reverse("api-article-subscribed"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(unapproved.id, [a["id"] for a in response.data])

    def test_unauthenticated_cannot_access_subscribed_feed(self):
        response = APIClient().get(reverse("api-article-subscribed"))
        self.assertEqual(response.status_code, 401)


# 6. Newsletters
class NewsletterTests(TestCase):

    def setUp(self):
        self.journalist, _ = make_user("nl_journalist", "Journalist")
        self.editor, _ = make_user("nl_editor", "Editor")
        self.reader, _ = make_user("nl_reader", "Reader")
        self.other_journalist, _ = make_user("nl_j2", "Journalist")

        self.newsletter = Newsletter.objects.create(
            title="Weekly Digest",
            description="Best of the week.",
            author=self.journalist.username,
        )
        self.newsletter.journalist_authors.add(self.journalist)

    def test_reader_can_view_newsletters(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse("newsletter-list"))
        self.assertEqual(response.status_code, 200)

    def test_journalist_can_create_newsletter(self):
        self.client.force_login(self.journalist)
        response = self.client.post(reverse("newsletter-create"), {
            "title": "New Newsletter", "description": "Fresh.", "articles": [],
        })
        self.assertIn(response.status_code, [200, 302])

    def test_reader_cannot_create_newsletter(self):
        self.client.force_login(self.reader)
        response = self.client.post(reverse("newsletter-create"), {
            "title": "Sneaky", "description": "Nope.",
        })
        self.assertEqual(response.status_code, 403)

    def test_journalist_cannot_edit_another_journalists_newsletter(self):
        self.client.force_login(self.other_journalist)
        response = self.client.post(
            reverse("newsletter-update", kwargs={"pk": self.newsletter.pk}),
            {"title": "Takeover", "description": "No.", "articles": []},
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_delete_any_newsletter(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("newsletter-delete", kwargs={"pk": self.newsletter.pk})
        )
        self.assertIn(response.status_code, [200, 302])


# 7. Approval email logic (mocked)
class ApprovalEmailTests(TestCase):

    def setUp(self):
        self.editor, _ = make_user("ed_mail", "Editor")
        self.journalist, _ = make_user("jo_mail", "Journalist")
        self.article = make_article(self.journalist, approved=False)

    @patch("NewsApp.views.send_mail")
    def test_approval_sends_email_to_article_author(self, mock_send_mail):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("article_approve", kwargs={"pk": self.article.pk}),
            {"approved": "on", "feedback": ""},
        )
        self.article.refresh_from_db()
        self.assertTrue(mock_send_mail.called)

    @patch("NewsApp.views.send_mail")
    def test_non_editor_approval_attempt_does_not_send_email(self, mock_send_mail):
        reader, _ = make_user("reader_mail", "Reader")
        self.client.force_login(reader)
        self.client.post(
            reverse("article_approve", kwargs={"pk": self.article.pk}),
            {"approved": "on"},
        )
        mock_send_mail.assert_not_called()
