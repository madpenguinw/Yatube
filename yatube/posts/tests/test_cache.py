from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Mikhail')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_cache(self):
        response = CacheTests.authorized_client.get(reverse('posts:index'))
        data = response.content
        Post.objects.create(
            author=self.user,
            text='Какой-либо текст',
        )
        new_response = CacheTests.authorized_client.get(reverse('posts:index'))
        new_data = new_response.content
        self.assertEqual(data, new_data)
        cache.clear()
        response_after_cleansing = CacheTests.authorized_client.get(reverse(
            'posts:index'))
        data_after_cleansing = response_after_cleansing.content
        self.assertNotEqual(new_data, data_after_cleansing)
