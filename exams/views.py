from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Exam, Question, Option, StudentExamAttempt
from .forms import ExamForm, QuestionForm, OptionForm

def is_faculty(user):
    return user.is_faculty()

@login_required
def exam_list(request):
    if request.user.is_faculty():
        exams = Exam.objects.all() # Or filter by faculty if needed
    else:
        exams = Exam.objects.filter(is_active=True)
    return render(request, 'exams/exam_list.html', {'exams': exams})

@login_required
@user_passes_test(is_faculty)
def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = ExamForm()
    return render(request, 'exams/exam_form.html', {'form': form})

@login_required
def exam_detail(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    return render(request, 'exams/exam_detail.html', {'exam': exam})

@login_required
@user_passes_test(is_faculty)
def add_question(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        # We need a way to add options too. For simplicity, let's just add question text and 4 options manually or generic.
        # But wait, we need OptionForm.
        # Let's simple it: Just save the question.
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            
            # Create Options
            correct_option_index = request.POST.get('correct_option')
            for i in range(1, 5):
                option_text = request.POST.get(f'option_{i}')
                if option_text:
                    is_correct = (str(i) == correct_option_index)
                    Option.objects.create(question=question, text=option_text, is_correct=is_correct)
            
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = QuestionForm()
    return render(request, 'exams/question_form.html', {'form': form, 'exam': exam})

@login_required
def take_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    # Check if attempt exists
    attempt, created = StudentExamAttempt.objects.get_or_create(
        student=request.user,
        exam=exam
    )

    # Check if system check is pending (simple logic: referer check or session)
    # For now, let's just create a new view for starting the flow or rely on URL changes in templates.
    # Actually, let's redirect to system check if not visited recently? 
    # Simpler: The "Take Exam" button in dashboard will now point to 'system_check'.
    # And 'system_check' template points to here.
    
    if attempt.is_completed:
        return render(request, 'exams/exam_result.html', {'attempt': attempt})
    
    mobile_url = request.build_absolute_uri(f'/proctoring/mobile/{attempt.id}/')
    return render(request, 'exams/take_exam.html', {'exam': exam, 'attempt': attempt, 'mobile_url': mobile_url})

def redirect_to_system_check(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    attempt, created = StudentExamAttempt.objects.get_or_create(
        student=request.user,
        exam=exam
    )
    if attempt.is_completed:
        return redirect('exam_result', pk=pk)
        
    return redirect('system_check', attempt_id=attempt.id)
    exam = get_object_or_404(Exam, pk=pk)
    # Check if attempt exists
    attempt, created = StudentExamAttempt.objects.get_or_create(
        student=request.user,
        exam=exam
    )
    if attempt.is_completed:
        return render(request, 'exams/exam_result.html', {'attempt': attempt})
    
    return render(request, 'exams/take_exam.html', {'exam': exam, 'attempt': attempt})

@login_required
def submit_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    attempt = get_object_or_404(StudentExamAttempt, student=request.user, exam=exam)
    
    if request.method == 'POST':
        score = 0
        total_questions = exam.questions.count()
        
        for question in exam.questions.all():
            selected_option_id = request.POST.get(f'q_{question.id}')
            if selected_option_id:
                option = Option.objects.get(id=selected_option_id)
                if option.is_correct:
                    score += question.marks
        
        attempt.score = score
        attempt.is_completed = True
        attempt.save()
        return redirect('exam_result', pk=exam.pk) # You might need a URL for this too, or reuse detail?
        # Let's create a dedicated result view or reuse detail with context. 
        # I'll redirect to a new view 'exam_result_view'
    return redirect('dashboard')

@login_required
def exam_result_view(request, pk):
    # This is a bit redundant with exam_detail logic but distinct for "result" page
    attempt = get_object_or_404(StudentExamAttempt, exam__pk=pk, student=request.user)
    return render(request, 'exams/exam_result.html', {'attempt': attempt})
