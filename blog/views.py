from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import BlogPost

class PostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        # Only show active posts published in the past/present
        return BlogPost.objects.filter(
            is_active=True, 
            published_at__lte=timezone.now()
        ).order_by('-published_at')


class PostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        # Restrict detail view to active, published posts
        return BlogPost.objects.filter(
            is_active=True,
            published_at__lte=timezone.now()
        )
