from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'dashboard/dashboard.html')


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'dashboard/profile.html')
