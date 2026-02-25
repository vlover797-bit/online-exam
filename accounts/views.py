from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

from exams.models import Exam, StudentExamAttempt
from proctoring.models import ProctorLog
from .models import User

@login_required
def dashboard(request):
    if request.user.is_student():
        return render(request, 'accounts/student_dashboard.html')
    elif request.user.is_faculty():
        # Fetch Stats
        total_students = User.objects.filter(role='student').count()
        total_exams = Exam.objects.count()
        total_attempts = StudentExamAttempt.objects.count()
        recent_violations = ProctorLog.objects.order_by('-timestamp')[:10]
        
        # Data for tables
        students = User.objects.filter(role='student')
        exams = Exam.objects.all().order_by('-start_time')
        recent_attempts = StudentExamAttempt.objects.select_related('student', 'exam').order_by('-end_time')[:10]

        context = {
            'total_students': total_students,
            'total_exams': total_exams,
            'total_attempts': total_attempts,
            'recent_violations': recent_violations,
            'students': students,
            'exams': exams,
            'recent_attempts': recent_attempts,
        }
        return render(request, 'accounts/faculty_dashboard.html', context)
    else:
        return render(request, 'accounts/admin_dashboard.html') # or redirect to admin
