from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Bookmark, Category, Comment, Like, Post, Tag
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    CommentWriteSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
    TagSerializer,
)


def get_post_queryset():
    return Post.objects.select_related('author', 'category').prefetch_related('tags')


def filter_published_posts(queryset, query_params):
    category = query_params.get('category')
    tag = query_params.get('tag')
    author = query_params.get('author')
    search = query_params.get('search')

    if category:
        queryset = queryset.filter(category__slug=category)
    if tag:
        queryset = queryset.filter(tags__slug=tag)
    if author:
        queryset = queryset.filter(author__username=author)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(content__icontains=search)
            | Q(excerpt__icontains=search)
        )

    return queryset.distinct()


def paginate_posts(request, queryset, serializer_class):
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list_view(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def tag_list_view(request):
    tags = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_list_create_view(request):
    if request.method == 'GET':
        queryset = get_post_queryset().filter(status=Post.Status.PUBLISHED)
        queryset = filter_published_posts(queryset, request.query_params)
        return paginate_posts(request, queryset, PostListSerializer)

    serializer = PostWriteSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    post = serializer.save(author=request.user)

    return Response(
        PostDetailSerializer(post, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_posts_view(request):
    queryset = get_post_queryset().filter(author=request.user)
    return paginate_posts(request, queryset, PostDetailSerializer)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def post_detail_view(request, slug):
    queryset = get_post_queryset()

    if request.method == 'GET':
        if request.user.is_authenticated:
            post = get_object_or_404(
                queryset.filter(Q(status=Post.Status.PUBLISHED) | Q(author=request.user)),
                slug=slug,
            )
        else:
            post = get_object_or_404(
                queryset.filter(status=Post.Status.PUBLISHED),
                slug=slug,
            )
        return Response(PostDetailSerializer(post, context={'request': request}).data)

    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    post = get_object_or_404(queryset, slug=slug)
    if post.author != request.user:
        return Response(
            {'detail': 'You do not have permission to modify this post.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PostWriteSerializer(
        post,
        data=request.data,
        partial=True,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    post = serializer.save()

    return Response(PostDetailSerializer(post, context={'request': request}).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_comments_view(request, slug):
    post = get_object_or_404(
        get_post_queryset().filter(status=Post.Status.PUBLISHED),
        slug=slug,
    )

    if request.method == 'GET':
        comments = post.comments.select_related('user')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = CommentWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    comment = serializer.save(post=post, user=request.user)

    return Response(
        CommentSerializer(comment, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_detail_view(request, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related('post', 'user'),
        pk=comment_id,
    )

    if comment.user != request.user:
        return Response(
            {'detail': 'You do not have permission to modify this comment.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CommentWriteSerializer(comment, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    comment = serializer.save()

    return Response(CommentSerializer(comment, context={'request': request}).data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_like_view(request, slug):
    post = get_object_or_404(
        get_post_queryset().filter(status=Post.Status.PUBLISHED),
        slug=slug,
    )

    like = Like.objects.filter(post=post, user=request.user).first()

    if request.method == 'POST':
        if like:
            like.delete()
            liked = False
            message = 'Post unliked successfully.'
        else:
            Like.objects.create(post=post, user=request.user)
            liked = True
            message = 'Post liked successfully.'

        return Response(
            {
                'message': message,
                'liked': liked,
                'like_count': post.likes.count(),
            }
        )

    if like:
        like.delete()

    return Response(
        {
            'message': 'Post unliked successfully.',
            'liked': False,
            'like_count': post.likes.count(),
        }
    )


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_bookmark_view(request, slug):
    post = get_object_or_404(
        get_post_queryset().filter(status=Post.Status.PUBLISHED),
        slug=slug,
    )

    bookmark = Bookmark.objects.filter(post=post, user=request.user).first()

    if request.method == 'POST':
        if bookmark:
            message = 'Post already bookmarked.'
        else:
            Bookmark.objects.create(post=post, user=request.user)
            message = 'Post bookmarked successfully.'

        return Response(
            {
                'message': message,
                'bookmarked': True,
                'post': PostListSerializer(post, context={'request': request}).data,
            }
        )

    if bookmark:
        bookmark.delete()

    return Response(
        {
            'message': 'Post removed from bookmarks successfully.',
            'bookmarked': False,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bookmark_list_view(request):
    queryset = get_post_queryset().filter(
        bookmarks__user=request.user,
        status=Post.Status.PUBLISHED,
    )
    return paginate_posts(request, queryset, PostListSerializer)
