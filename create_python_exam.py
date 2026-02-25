import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from exams.models import Exam, Question, Option

def create_exam():
    # Exam Details
    title = "Python Programming Language"
    description = "A comprehensive assessment of Python programming concepts, covering syntax, data structures, functions, OOP, and libraries."
    duration_minutes = 180
    start_time = timezone.now() + timedelta(minutes=10) # Starts in 10 mins
    end_time = start_time + timedelta(hours=4) # Open for 4 hours window
    
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

    # Questions Data (20 Questions, 5 marks each)
    questions_data = [
        {
            "text": "What is the correct file extension for Python files?",
            "marks": 5,
            "options": [
                {"text": ".py", "is_correct": True},
                {"text": ".python", "is_correct": False},
                {"text": ".pyt", "is_correct": False},
                {"text": ".pt", "is_correct": False}
            ]
        },
        {
            "text": "Which keyword is used to define a function in Python?",
            "marks": 5,
            "options": [
                {"text": "func", "is_correct": False},
                {"text": "def", "is_correct": True},
                {"text": "define", "is_correct": False},
                {"text": "function", "is_correct": False}
            ]
        },
        {
            "text": "How do you insert comments in Python code?",
            "marks": 5,
            "options": [
                {"text": "// This is a comment", "is_correct": False},
                {"text": "# This is a comment", "is_correct": True},
                {"text": "/* This is a comment */", "is_correct": False},
                {"text": "<!-- This is a comment -->", "is_correct": False}
            ]
        },
        {
            "text": "Which collection is ordered, changeable, and allows duplicate members?",
            "marks": 5,
            "options": [
                {"text": "Set", "is_correct": False},
                {"text": "Dictionary", "is_correct": False},
                {"text": "Tuple", "is_correct": False},
                {"text": "List", "is_correct": True}
            ]
        },
        {
            "text": "What is the output of: print(2 ** 3)?",
            "marks": 5,
            "options": [
                {"text": "6", "is_correct": False},
                {"text": "8", "is_correct": True},
                {"text": "9", "is_correct": False},
                {"text": "5", "is_correct": False}
            ]
        },
        {
            "text": "Which method can be used to return a string in upper case letters?",
            "marks": 5,
            "options": [
                {"text": "upper()", "is_correct": True},
                {"text": "uppercase()", "is_correct": False},
                {"text": "toUpperCase()", "is_correct": False},
                {"text": "upperCase()", "is_correct": False}
            ]
        },
        {
            "text": "Which operator is used for floor division?",
            "marks": 5,
            "options": [
                {"text": "/", "is_correct": False},
                {"text": "%", "is_correct": False},
                {"text": "//", "is_correct": True},
                {"text": "#", "is_correct": False}
            ]
        },
        {
            "text": "What is the correct way to create a dictionary?",
            "marks": 5,
            "options": [
                {"text": "{'a', 'b', 'c'}", "is_correct": False},
                {"text": "('name': 'John')", "is_correct": False},
                {"text": "{'name': 'John', 'age': 30}", "is_correct": True},
                {"text": "['name': 'John']", "is_correct": False}
            ]
        },
        {
            "text": "Which of these is NOT a core data type in Python?",
            "marks": 5,
            "options": [
                {"text": "List", "is_correct": False},
                {"text": "Dictionary", "is_correct": False},
                {"text": "Tuple", "is_correct": False},
                {"text": "Class", "is_correct": True}
            ]
        },
        {
            "text": "What is the output of type([1, 2])?",
            "marks": 5,
            "options": [
                {"text": "<class 'tuple'>", "is_correct": False},
                {"text": "<class 'list'>", "is_correct": True},
                {"text": "<class 'set'>", "is_correct": False},
                {"text": "<class 'dict'>", "is_correct": False}
            ]
        },
        {
            "text": "Which loop is used to iterate over a sequence?",
            "marks": 5,
            "options": [
                {"text": "while", "is_correct": False},
                {"text": "for", "is_correct": True},
                {"text": "do-while", "is_correct": False},
                {"text": "loop", "is_correct": False}
            ]
        },
        {
            "text": "How do you handle exceptions in Python?",
            "marks": 5,
            "options": [
                {"text": "try...except", "is_correct": True},
                {"text": "do...catch", "is_correct": False},
                {"text": "try...catch", "is_correct": False},
                {"text": "catch...throw", "is_correct": False}
            ]
        },
        {
            "text": "Which module in Python supports regular expressions?",
            "marks": 5,
            "options": [
                {"text": "regex", "is_correct": False},
                {"text": "re", "is_correct": True},
                {"text": "pyregex", "is_correct": False},
                {"text": "string", "is_correct": False}
            ]
        },
        {
            "text": "What is the result of 'Hello'[1]?",
            "marks": 5,
            "options": [
                {"text": "H", "is_correct": False},
                {"text": "e", "is_correct": True},
                {"text": "l", "is_correct": False},
                {"text": "o", "is_correct": False}
            ]
        },
        {
            "text": "Which keyword is used to import a module?",
            "marks": 5,
            "options": [
                {"text": "include", "is_correct": False},
                {"text": "using", "is_correct": False},
                {"text": "import", "is_correct": True},
                {"text": "from", "is_correct": False}
            ]
        },
        {
            "text": "What is the correct syntax to output 'Hello World' in Python 3?",
            "marks": 5,
            "options": [
                {"text": "echo 'Hello World'", "is_correct": False},
                {"text": "print('Hello World')", "is_correct": True},
                {"text": "p('Hello World')", "is_correct": False},
                {"text": "printf('Hello World')", "is_correct": False}
            ]
        },
        {
            "text": "Which of the following is immutable?",
            "marks": 5,
            "options": [
                {"text": "List", "is_correct": False},
                {"text": "Dictionary", "is_correct": False},
                {"text": "Set", "is_correct": False},
                {"text": "Tuple", "is_correct": True}
            ]
        },
        {
            "text": "What does the len() function do?",
            "marks": 5,
            "options": [
                {"text": "Returns the length of an object", "is_correct": True},
                {"text": "Returns the type of an object", "is_correct": False},
                {"text": "Returns the memory size", "is_correct": False},
                {"text": "Returns the last element", "is_correct": False}
            ]
        },
        {
            "text": "Which statement is used to stop a loop?",
            "marks": 5,
            "options": [
                {"text": "stop", "is_correct": False},
                {"text": "exit", "is_correct": False},
                {"text": "break", "is_correct": True},
                {"text": "return", "is_correct": False}
            ]
        },
        {
            "text": "What is the output of bool(0)?",
            "marks": 5,
            "options": [
                {"text": "True", "is_correct": False},
                {"text": "False", "is_correct": True},
                {"text": "None", "is_correct": False},
                {"text": "Error", "is_correct": False}
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
