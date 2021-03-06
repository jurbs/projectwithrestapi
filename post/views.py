from django.shortcuts import render
from rest_framework.decorators import permission_classes
from rest_framework.response import Response

from .models import PostInfo, Comment, Likes, Section
from rest_framework import generics, status
from .serializers import PostInfoSerializer, PostDetailSerializer, SectionCreateSerializer, AddCommentSerializer, \
    AddOrRemoveLikesSerializer, PostCreateSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import get_token
from django.http import HttpResponse


def get_csrf(request):
    return HttpResponse("{0}".format(get_token(request)), content_type="text/plain")


def post_info(request):
    posts = PostInfo.objects.all()
    return render(request, 'index1.html', {'posts': posts})


class PostDetail(generics.RetrieveAPIView):
    queryset = PostInfo.objects.all()
    serializer_class = PostDetailSerializer
    permission_classes = (AllowAny, )


class PostCreate(generics.CreateAPIView):
    queryset = PostInfo.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = (IsAuthenticated, )
    
    def post(self, request, *args, **kwargs):
        if post := request.data.get('title'):
            post = PostInfo.objects.create(title=post, author=request.user)
        else:
            return Response(data={'detail': 'Missing title data'})
        if sections := request.data.get('sections'):
            for item in sections:
                title = item.get('title')
                if not title:
                    return Response(data={'detail': 'Missing title data'})
                desc = item.get('content')
                if not desc:
                    return Response(data={'detail': 'Missing content data'})
                Section.objects.create(post_id=post, title=item.get('title') or None,
                                       content=item.get('content') or None,
                                       author=request.user)
        else:
            return Response(data={'detail': 'Missing sections data'})
        return Response(data={'post_id': post.id}, status=status.HTTP_200_OK)


class SectionCreate(generics.CreateAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionCreateSerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        post = PostInfo.objects.get(id=self.kwargs.get('post_id'))
        serializer.save(post_id=post)

    def create(self, request, *args, **kwargs):
        post = PostInfo.objects.get(id=self.kwargs.get('post_id'))
        if post.author == request.user:
            return super().create(request, *args, **kwargs)
        return Response(data={'error': 'invalid user'}, status=status.HTTP_401_UNAUTHORIZED)


class PostView(generics.ListAPIView):
    permission_classes = (AllowAny, )
    queryset = PostInfo.objects.all()
    serializer_class = PostInfoSerializer


class PostEdit(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostDetailSerializer
    queryset = PostInfo.objects.all()
    permission_classes = (IsOwnerOrReadOnly, IsAuthenticated)

    def delete(self, request, *args, **kwargs):
        post = self.kwargs.get('pk')
        Section.objects.filter(post_id=post or None).delete()
        Likes.objects.filter(post_id=post or None).delete()
        Comment.objects.filter(post_id=post or None).delete()
        return super(PostEdit, self).delete(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        ''' Trying to get sections '''
        if sections := request.data.get('sections'):
            for item in sections:
                title = item.get('title')
                content = item.get('content')
                if id := item.get('id'):
                    if section := Section.objects.filter(id=id):
                        ''' Delete sections '''
                        if item.get('delete'):
                            section.delete()
                            continue

                        ''' Update sections '''
                        section.update(title=title or None, content=content or None)
                    else:
                        return Response(data={'detail': 'section with that id does not exist'})
                else:
                    ''' Create sections '''
                    if not title:
                        return Response(data={'detail': 'Missing title data'})
                    if not content:
                        return Response(data={'detail': 'Missing content data'})
                    Section.objects.create(title=title, content=content, post_id=PostInfo.objects.get(id=self.kwargs.get('pk')), author=request.user)
        return super(PostEdit, self).put(request, *args, **kwargs)


class AddComment(generics.CreateAPIView):
    serializer_class = AddCommentSerializer
    queryset = Comment.objects.all()
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        post = PostInfo.objects.get(id=self.kwargs.get('comment_id'))
        serializer.save(post_id=post)

    # def get_queryset(self):
    #     return super().get_queryset().filter(post=self.kwargs.get('post_id'))


class UpdateDeleteComment(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddCommentSerializer
    queryset = Comment.objects.all()
    permission_classes = (IsOwnerOrReadOnly, )


class AddLikes(generics.CreateAPIView):
    serializer_class = AddOrRemoveLikesSerializer
    queryset = Likes.objects.all()
    permission_classes(IsAuthenticated, )

    def perform_create(self, serializer):
        post = PostInfo.objects.get(id=self.kwargs.get('post_id'))
        serializer.save(post_id=post)

    def post(self, request, *args, **kwargs):
        user = request.user
        if like := Likes.objects.filter(author=user, post_id_id=self.kwargs.get('post_id')):
            like.delete()
            return Response(data={'delete': 'successfully'}, status=status.HTTP_200_OK)
        return super(AddLikes, self).post(request, *args, **kwargs)