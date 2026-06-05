from django.urls import path

from . import views

urlpatterns = [
    path('categories/', views.category_list_view, name='category-list'),
    path('tags/', views.tag_list_view, name='tag-list'),
    path('posts/', views.post_list_create_view, name='post-list-create'),
    path('bookmarks/', views.bookmark_list_view, name='bookmark-list'),
    path('posts/my-posts/', views.my_posts_view, name='my-posts'),
    path('posts/<slug:slug>/comments/', views.post_comments_view, name='post-comments'),
    path('posts/<slug:slug>/like/', views.post_like_view, name='post-like'),
    path('posts/<slug:slug>/bookmark/', views.post_bookmark_view, name='post-bookmark'),
    path('posts/<slug:slug>/', views.post_detail_view, name='post-detail'),
    path('comments/<int:comment_id>/', views.comment_detail_view, name='comment-detail'),
]
