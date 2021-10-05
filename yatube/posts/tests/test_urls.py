from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_but_not_author = User.objects.create_user(
            username='Mikhail_Sokolov'
        )
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.authorized_but_not_author)
        cls.author = User.objects.create_user(username='Mikhail')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Какой-нибудь заголовок',
            description='Какое-нибудь описание',
            slug='slug',
        )
        cls.post = Post.objects.create(
            text='Какой-нибудь текст',
            author=cls.author,
            group=cls.group,
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = [
            {
                'route': 'posts/index.html',
                'reverse': reverse('posts:index'),
            },
            {
                'route': 'posts/group_list.html',
                'reverse': reverse(
                    'posts:group_posts',
                    kwargs={'slug': PostURLTests.group.slug}
                ),
            },
            {
                'route': 'posts/profile.html',
                'reverse': reverse(
                    'posts:profile',
                    kwargs={'username': PostURLTests.author}
                ),
            },
            {
                'route': 'posts/post_detail.html',
                'reverse': reverse(
                    'posts:post_detail',
                    kwargs={'post_id': PostURLTests.post.id}
                ),
            },
            {
                'route': 'posts/create_post.html',
                'reverse': reverse('posts:create'),
            },
            {
                'route': 'posts/create_post.html',
                'reverse': reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id}
                ),
            },
        ]
        for templates_pages_name in templates_pages_names:
            with self.subTest(
                    reverse_name=templates_pages_name.get('reverse')):
                response = self.author_client.get(
                    templates_pages_name.get('reverse'))
                self.assertTemplateUsed(
                    response, templates_pages_name.get('route'))

    def test_create_post_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = PostURLTests.guest_client.get(reverse(
            'posts:create'),
            follow=True
        )
        self.assertRedirects(response,
                             reverse('users:login') + '?next=' + reverse(
                                 'posts:create'))

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /post_edit/ перенаправляет анонимного
        пользователя.
        """
        response = PostURLTests.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.id}
            ),
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login') + '?next=' + reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.id}
            )
        )

    def test_post_edit_url_redirect_authorized_but_not_author(self):
        """Страница /post_edit/ перенаправляет авторизованного
        пользователя, не являющегося автором.
        """
        response = PostURLTests.not_author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.id})
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostURLTests.post.id})
        )

    def test_wrong_url_page(self):
        """Запрос к несуществующей странице возвращает ошибку 404."""
        response = self.client.get('/this_should_not_work/')
        self.assertEqual(response.status_code, 404)
