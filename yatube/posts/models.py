from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Название группы'
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        db_index=True,
        verbose_name='URL группы'
    )
    description = models.TextField(
        verbose_name='Описание группы'
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='*Обязательное поле'
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        related_name='posts',
        on_delete=models.SET_NULL,
        verbose_name='Выберите группу из списка',
        help_text='Выберите группу'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Комментарий поста',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        verbose_name='Текст нового комментария',
        help_text='*Обязательное поле'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Коментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        db_table = 'follow'
        constraints = [
            models.UniqueConstraint(fields=['author', 'user'],
                                    name='unique_followed_author')
        ]
