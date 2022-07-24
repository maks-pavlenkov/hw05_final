from http import HTTPStatus
from django.test import TestCase, Client
from django.core.cache import cache
from posts.models import Post, Group, User


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        cls.post = Post.objects.create(
            text='TEST POST! with 15 or more chars',
            author=cls.user,
            group=cls.group
        )
        cls.urls = [
            '/',
            '/group/test_slug/',
            '/profile/test_user/',
            '/posts/1/',
            '/posts/1/edit/',
            '/create/',
            '/unexisting_page/']

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Автор поста
        self.authorized_client_author.force_login(TaskURLTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': ''
        }
        for url, template in templates_url_names.items():
            if url != '/unexisting_page/':
                with self.subTest(url=url):
                    response = self.authorized_client_author.get(url)
                    self.assertTemplateUsed(response, template)

    def test_accesses_for_guest_user(self):
        """Все доступы к страницам корректны."""
        user = self.guest_client
        for url in self.urls:
            with self.subTest(url=url):
                if url in ('/posts/1/edit/', '/create/'):
                    response = user.get(url, follow=True)
                    self.assertRedirects(
                        response,
                        '/auth/login/?next=/create/'
                        if url == '/create/'
                        else '/auth/login/?next=/posts/1/edit/')
                elif url == '/unexisting_page/':
                    response = user.get(url)
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )
                else:
                    response = user.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_accesses_for_auth_user(self):
        user = self.authorized_client
        for url in self.urls:
            with self.subTest(url=url):
                if user == self.authorized_client:
                    if url == '/posts/1/edit/':
                        response = user.get(url, follow=True)
                        self.assertRedirects(
                            response,
                            '/posts/1/'
                        )
                    elif url == '/unexisting_page/':
                        response = user.get(url)
                        self.assertEqual(
                            response.status_code, HTTPStatus.NOT_FOUND
                        )
                    else:
                        response = user.get(url)
                        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_accesses_for_auth_author_user(self):
        user = self.authorized_client_author
        for url in self.urls:
            with self.subTest(url=url):
                if user == self.authorized_client_author:
                    if url != '/unexisting_page/':
                        response = user.get(url)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
                    else:
                        response = user.get(url)
                        self.assertEqual(
                            response.status_code, HTTPStatus.NOT_FOUND
                        )
