import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from exams.models import Exam, Question, Option

def create_exam():
    # Exam Details
    title = "General Knowledge Quiz"
    description = "Test your general knowledge with these 10 questions covering various topics."
    duration_minutes = 60
    start_time = timezone.now() + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=24)
    
    # Check if exam exists
    if Exam.objects.filter(title=title).exists():
        print(f"Exam '{title}' already exists.")
        return

    # Create Exam
    exam = Exam.objects.create(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        is_active=True
    )
    print(f"Created Exam: {exam.title}")

    # Questions Data (10 Questions, 10 marks each)
    questions_data = [
        {
            "text": "What is the largest planet in our solar system?",
            "marks": 10,
            "options": [
                {"text": "Earth", "is_correct": False},
                {"text": "Jupiter", "is_correct": True},
                {"text": "Saturn", "is_correct": False},
                {"text": "Mars", "is_correct": False}
            ]
        },
        {
            "text": "Who wrote 'Romeo and Juliet'?",
            "marks": 10,
            "options": [
                {"text": "Charles Dickens", "is_correct": False},
                {"text": "William Shakespeare", "is_correct": True},
                {"text": "Mark Twain", "is_correct": False},
                {"text": "Jane Austen", "is_correct": False}
            ]
        },
        {
            "text": "What is the chemical symbol for Gold?",
            "marks": 10,
            "options": [
                {"text": "Au", "is_correct": True},
                {"text": "Ag", "is_correct": False},
                {"text": "Fe", "is_correct": False},
                {"text": "Pb", "is_correct": False}
            ]
        },
        {
            "text": "Which continent is the Sahara Desert located in?",
            "marks": 10,
            "options": [
                {"text": "Asia", "is_correct": False},
                {"text": "Africa", "is_correct": True},
                {"text": "South America", "is_correct": False},
                {"text": "Australia", "is_correct": False}
            ]
        },
        {
            "text": "What is the capital of Japan?",
            "marks": 10,
            "options": [
                {"text": "Seoul", "is_correct": False},
                {"text": "Beijing", "is_correct": False},
                {"text": "Tokyo", "is_correct": True},
                {"text": "Bangkok", "is_correct": False}
            ]
        },
        {
            "text": "How many players are there in a standard soccer team?",
            "marks": 10,
            "options": [
                {"text": "10", "is_correct": False},
                {"text": "11", "is_correct": True},
                {"text": "12", "is_correct": False},
                {"text": "9", "is_correct": False}
            ]
        },
        {
            "text": "Which element is needed for combustion?",
            "marks": 10,
            "options": [
                {"text": "Carbon", "is_correct": False},
                {"text": "Nitrogen", "is_correct": False},
                {"text": "Oxygen", "is_correct": True},
                {"text": "Hydrogen", "is_correct": False}
            ]
        },
        {
            "text": "What is the hardest natural substance on Earth?",
            "marks": 10,
            "options": [
                {"text": "Gold", "is_correct": False},
                {"text": "Iron", "is_correct": False},
                {"text": "Diamond", "is_correct": True},
                {"text": "Platinum", "is_correct": False}
            ]
        },
        {
            "text": "Who painted the Mona Lisa?",
            "marks": 10,
            "options": [
                {"text": "Vincent van Gogh", "is_correct": False},
                {"text": "Pablo Picasso", "is_correct": False},
                {"text": "Leonardo da Vinci", "is_correct": True},
                {"text": "Claude Monet", "is_correct": False}
            ]
        },
        {
            "text": "What does HTTP stand for?",
            "marks": 10,
            "options": [
                {"text": "HyperText Transfer Protocol", "is_correct": True},
                {"text": "HyperText Transmission Protocol", "is_correct": False},
                {"text": "HighText Transfer Protocol", "is_correct": False},
                {"text": "HyperText Transfer Program", "is_correct": False}
            ]
        }
    ]

    # Create Questions and Options
    for q_data in questions_data:
        question = Question.objects.create(
            exam=exam,
            text=q_data["text"],
            marks=q_data["marks"]
        )
        for opt_data in q_data["options"]:
            Option.objects.create(
                question=question,
                text=opt_data["text"],
                is_correct=opt_data["is_correct"]
            )
    
    print(f"Successfully added {len(questions_data)} questions to the exam.")

if __name__ == '__main__':
    create_exam()
