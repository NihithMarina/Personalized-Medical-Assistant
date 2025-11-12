from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def home(request):
    """Home page view"""
    # Show the public homepage for everyone.
    # Previously this redirected authenticated users to dashboards; keep the homepage as the entry point.
    return render(request, 'home.html')

def login_view(request):
    """Login view for both patients and doctors"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST['user_type']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user belongs to the selected user type
            if user_type == 'patient' and user.groups.filter(name='Patients').exists():
                login(request, user)
                return redirect('patients:dashboard')
            elif user_type == 'doctor' and user.groups.filter(name='Doctors').exists():
                login(request, user)
                return redirect('doctors:dashboard')
            else:
                messages.error(request, 'Invalid user type selected.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def register_view(request):
    """Registration view for both patients and doctors"""
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        user_type = request.POST['user_type']
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'auth/register.html')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Add user to appropriate group
        if user_type == 'patient':
            group, created = Group.objects.get_or_create(name='Patients')
            user.groups.add(group)
            messages.success(request, 'Patient account created successfully. Please login.')
        elif user_type == 'doctor':
            group, created = Group.objects.get_or_create(name='Doctors')
            user.groups.add(group)
            messages.success(request, 'Doctor account created successfully. Please login.')
        
        return redirect('login')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    # After logout, return to the public homepage.
    return redirect('home')