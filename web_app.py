import os
import time

from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, session, flash
)
from dotenv import load_dotenv
from google import genai

from auth import register_student, login_student
from history import save_prompt_history, get_prompt_history

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# ---------------- HOME ----------------

@app.route("/")
def home():
    if session.get("student_id"):
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")

        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")

        else:
            success, message = register_student(
                name, email, password
            )

            if success:
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))

            flash(message, "error")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        student = login_student(email, password)

        if student:
            session.clear()
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if not session.get("student_id"):
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        student_name=session.get("student_name")
    )

# ---------------- PROMPT HISTORY ----------------

@app.route("/history")
def prompt_history():

    if not session.get("student_id"):
        return redirect(url_for("login"))

    history = get_prompt_history(session["student_id"])

    return render_template(
        "history.html",
        history=history
    )

# ---------------- TOPIC EXPLANATION ----------------

@app.route("/topic", methods=["GET", "POST"])
def topic_explanation():

    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":

        topic = request.form.get("topic", "").strip()

        if not topic:
            error = "Please enter a topic."

        elif client is None:
            answer = get_demo_answer(topic)

        else:
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"""
Explain this Engineering topic in simple language.

Include:
1. Definition
2. Explanation
3. Important Points
4. Example
5. Applications
6. Conclusion

Topic: {topic}
"""
                )

                answer = response.text or get_demo_answer(topic)

            except Exception as e:

                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    answer = get_demo_answer(topic)
                else:
                    answer = get_demo_answer(topic)

        if answer:
            save_prompt_history(
                session["student_id"],
                f"Topic Explanation: {topic}",
                answer
            )
    return render_template(
        "topic.html",
        answer=answer,
        error=error
    )


# ---------------- DEMO ANSWERS ----------------

def get_demo_answer(topic):

    topic_lower = topic.lower()

    if "operating system" in topic_lower or topic_lower == "os":

        return """
DEMO MODE - Sample Answer

1. Definition:
An Operating System is system software that manages computer hardware
and software resources.

2. Explanation:
It acts as an interface between the user and computer hardware.

3. Important Points:
- Process Management
- Memory Management
- File Management
- Device Management

4. Example:
Windows, Linux and macOS.

5. Applications:
Used in computers, laptops and servers.

6. Conclusion:
An Operating System helps users operate a computer efficiently.
"""

    elif "dbms" in topic_lower or "database" in topic_lower:

        return """
DEMO MODE - Sample Answer

1. Definition:
DBMS stands for Database Management System.

2. Explanation:
It is software used to store, manage and retrieve data.

3. Important Points:
- Data Storage
- Data Security
- Data Retrieval
- Data Backup

4. Example:
MySQL, Oracle and PostgreSQL.

5. Applications:
Banking, hospitals and college management systems.

6. Conclusion:
DBMS helps organize and manage data efficiently.
"""

    elif "python" in topic_lower:

        return """
DEMO MODE - Sample Answer

1. Definition:
Python is a high-level programming language.

2. Explanation:
It has simple syntax and is used for developing different applications.

3. Important Points:
- Easy to Learn
- Object-Oriented
- Interpreted Language
- Large Libraries

4. Example:
print("Hello World")

5. Applications:
AI, Machine Learning, Web Development and Data Science.

6. Conclusion:
Python is a popular and beginner-friendly programming language.
"""

    else:

        return f"""
DEMO MODE - Sample Answer

Topic: {topic}

1. Definition:
This topic is an important concept in Engineering.

2. Explanation:
It helps students understand the basic principles and working
of the subject.

3. Important Points:
- Understand the basic concepts.
- Study its features.
- Learn its working.
- Understand practical applications.

4. Example:
Refer to a practical example from your subject textbook.

5. Applications:
This concept is useful in Engineering and Technology.

6. Conclusion:
Understanding this topic helps build strong subject knowledge.

Note: This is a sample Demo Mode answer, not a Gemini-generated answer.
"""
# QUESTION PAPER GENERATOR
@app.route("/question-paper", methods=["GET", "POST"])
def question_paper():
    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        marks = request.form.get("marks", "20")

        if not subject or not topic:
            error = "Please enter subject and topic."
        else:
            try:
                if client is None:
                    answer = get_demo_question_paper(
                        subject, topic, marks
                    )
                else:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=f"""
Create a practice question paper for engineering students.

Subject: {subject}
Topic: {topic}
Total Marks: {marks}

Include:
1. Instructions
2. Short answer questions
3. Long answer questions
4. Marks for each question
5. Total marks

Use simple English.
Make sure the total marks equal {marks}.
"""
                    )

                    answer = response.text or get_demo_question_paper(
                        subject, topic, marks
                    )

            except Exception:
                app.logger.exception("Question paper generation failed")
                answer = get_demo_question_paper(
                    subject, topic, marks
                )

        if request.method == "POST" and answer:
            save_prompt_history(
            session["student_id"],
            f"Question Paper: Subject: {subject}, Topic: {topic}, Marks: {marks}",
            answer
        )

    return render_template(
        "question_paper.html",
        answer=answer,
        error=error
    )

# DEMO QUESTION PAPER
def get_demo_question_paper(subject, topic, marks):
    return f"""
DEMO MODE - Sample Practice Question Paper

Subject: {subject}
Topic: {topic}
Total Marks: {marks}

Instructions:
1. Answer all questions.
2. Write answers in simple and clear language.

Q1. Answer the following questions. (2 Marks Each)
1. Define {topic}.
2. Explain the importance of {topic}.

Q2. Answer the following questions. (5 Marks Each)
1. Explain the features of {topic}.
2. Describe the working of {topic} with an example.

Q3. Write a detailed note on {topic}. (10 Marks)

Note: This is a sample Demo Mode question paper.
It is not generated by Gemini AI.
"""

# QUIZ GENERATOR
@app.route("/quiz", methods=["GET", "POST"])
def quiz_generator():
    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        num_questions = request.form.get("num_questions", "5")

        if not subject or not topic:
            error = "Please enter subject and topic."

        else:
            try:
                if client is None:
                    answer = get_demo_quiz(
                        subject, topic, num_questions
                    )
                else:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=f"""
You are an Engineering Quiz Generator.

Create {num_questions} multiple-choice questions.

Subject: {subject}
Topic: {topic}

For each question:
1. Give one question.
2. Provide four options (A, B, C, D).
3. Clearly mention the correct answer.
4. Add a short explanation.

Use simple English.
Number all questions correctly.
"""
                    )

                    answer = response.text or get_demo_quiz(
                        subject, topic, num_questions
                    )

            except Exception:
                app.logger.exception("Quiz generation failed")
                answer = get_demo_quiz(
                    subject, topic, num_questions
                )

        if request.method == "POST" and answer:
            save_prompt_history(
            session["student_id"],
            f"Quiz: Subject: {subject}, Topic: {topic}, Questions: {num_questions}",
            answer
        )

    return render_template(
        "quiz.html",
        answer=answer,
        error=error
    )

# DEMO QUIZ
def get_demo_quiz(subject, topic, num_questions):
    questions = []

    for i in range(int(num_questions)):
        questions.append(f"""
Q{i + 1}. What is an important concept related to {topic}?

A) Basic concept
B) Incorrect option
C) Unrelated concept
D) None of the above

Correct Answer: A) Basic concept

Explanation: This is a sample question related to {topic}.
""")

    return f"""
DEMO MODE - Sample Quiz

Subject: {subject}
Topic: {topic}
Total Questions: {num_questions}

{chr(10).join(questions)}

Note: This is a sample Demo Mode quiz.
It is not generated by Gemini AI.
"""

# FLASHCARD GENERATOR
@app.route("/flashcards", methods=["GET", "POST"])
def flashcard_generator():
    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        num_cards = request.form.get("num_cards", "5")

        if not subject or not topic:
            error = "Please enter subject and topic."
        else:
            try:
                if client is None:
                    answer = get_demo_flashcards(
                        subject, topic, num_cards
                    )
                else:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=f"""
You are an Engineering Study Flashcard Generator.

Create {num_cards} useful study flashcards.

Subject: {subject}
Topic: {topic}

For each flashcard include:
Flashcard number
Question
Answer

Use simple English.
Keep answers clear and useful for revision.
"""
                    )

                    answer = response.text or get_demo_flashcards(
                        subject, topic, num_cards
                    )

            except Exception:
                app.logger.exception("Flashcard generation failed")
                answer = get_demo_flashcards(
                    subject, topic, num_cards
                )

        if request.method == "POST" and answer:
            save_prompt_history(
            session["student_id"],
            f"Flashcards: Subject: {subject}, Topic: {topic}, Cards: {num_cards}",
            answer
        )

    return render_template(
        "flashcards.html",
        answer=answer,
        error=error
    )
    
# DEMO FLASHCARDS
def get_demo_flashcards(subject, topic, num_cards):
    cards = []

    for i in range(int(num_cards)):
        cards.append(f"""
FLASHCARD {i + 1}

Question:
What is {topic}?

Answer:
{topic} is an important concept in {subject}.
It helps students understand the basic working
and principles of the subject.
""")

    return f"""
DEMO MODE - Sample Flashcards

Subject: {subject}
Topic: {topic}
Total Flashcards: {num_cards}

{chr(10).join(cards)}

Note: These are sample Demo Mode flashcards.
They are not generated by Gemini AI.
"""


# -----# TEXT SUMMARIZER
@app.route("/summarizer", methods=["GET", "POST"])
def text_summarizer():
    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        summary_type = request.form.get(
            "summary_type", "Short Summary"
        )

        if not text:
            error = "Please enter some text to summarize."

        else:
            try:
                if client is None:
                    answer = get_demo_summary(text, summary_type)
                else:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=f"""
You are an AI Text Summarizer for Engineering students.

Summarize the following study material.

Summary Type: {summary_type}

Instructions:
- Use simple English.
- Keep the meaning accurate.
- Include important concepts.
- Use clear headings and bullet points.

Study Material:
{text}
"""
                    )

                    answer = response.text or get_demo_summary(
                        text, summary_type
                    )

            except Exception:
                app.logger.exception("Text summarization failed")
                answer = get_demo_summary(text, summary_type)

        if request.method == "POST" and answer:
            save_prompt_history(
            session["student_id"],
            f"Text Summarizer: {summary_type}\n{text}",
            answer
        )

    return render_template(
        "summarizer.html",
        answer=answer,
        error=error
    )
    
# DEMO SUMMARY
def get_demo_summary(text, summary_type):
    sentences = [
        sentence.strip()
        for sentence in text.replace("\n", " ").split(".")
        if sentence.strip()
    ]

    if summary_type == "Short Summary":
        selected = sentences[:3]
    elif summary_type == "Detailed Summary":
        selected = sentences[:6]
    else:
        selected = sentences[:5]

    return (
        "DEMO MODE - Sample Summary\n\n"
        + "\n".join(f"- {sentence}." for sentence in selected)
        + "\n\nNote: This is a sample Demo Mode summary. "
        "It is not generated by Gemini AI."   
    )
    
   # ----------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    flash("You have logged out successfully.", "success")

    return redirect(url_for("login"))

# ---------------- AI ASSISTANT PAGE ----------------

@app.route("/ai-assistant")
def ai_assistant():

    if not session.get("student_id"):
        return redirect(url_for("login"))

    return render_template("ai_assistant.html")

# ---------------- ASK AI ----------------

@app.route("/ask", methods=["POST"])
def ask():

    if not session.get("student_id"):
        return jsonify({"error": "Please login first."}), 401

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "Please enter your question."
        }), 400

    if client is None:
        return jsonify({
            "error": "GEMINI_API_KEY not found. Check your .env file."
        }), 500

    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"""
You are an AI Study Assistant for Engineering students.

Answer academic questions in simple language.

Follow this format:
1. Definition
2. Explanation
3. Examples
4. Applications
5. Conclusion

Question: {question}
"""
            )

            answer = response.text or "No answer received."

            save_prompt_history(
                session["student_id"],
                f"AI Assistant: {question}",
                answer
            )

            return jsonify({
                "answer": answer
            }), 200

            save_prompt_history(
                session["student_id"],
                f"AI Assistant: {question}",
                answer
            )

            return jsonify({
                "answer": answer
            }), 200
        except Exception as error:

            error_message = str(error)

            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                return jsonify({
                    "error": "Daily AI request limit reached. Please try again after your quota resets."
                }), 429

            if "503" in error_message and attempt < 2:
                time.sleep(5)
                continue

            app.logger.exception("Gemini API request failed")

            return jsonify({
                "error": "AI service is temporarily unavailable. Please try again later."
            }), 500

    return jsonify({
        "error": "Please try again later."
    }), 503

# ---------------- NOTES GENERATOR ----------------

@app.route("/notes", methods=["GET", "POST"])
def notes_generator():

    if not session.get("student_id"):
        return redirect(url_for("login"))

    answer = None
    error = None

    if request.method == "POST":

        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        note_type = request.form.get("note_type", "Short Notes")

        if not subject or not topic:
            error = "Please enter subject and topic."

        elif client is None:
            answer = get_demo_notes(subject, topic, note_type)

        else:
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"""
You are an Engineering Study Notes Generator.

Create {note_type} for the following:

Subject: {subject}
Topic: {topic}

Include:
1. Introduction
2. Definition
3. Important Points
4. Examples
5. Advantages
6. Conclusion

Use simple English and clear headings.
Make the notes useful for engineering students.
"""
                )

                answer = response.text or get_demo_notes(
                    subject, topic, note_type
                )

            except Exception:
                app.logger.exception("Notes generation failed")
                answer = get_demo_notes(subject, topic, note_type)

        if request.method == "POST" and answer:
            save_prompt_history(
            session["student_id"],
            f"Notes: Subject: {subject}, Topic: {topic}, Type: {note_type}",
            answer
        )

    return render_template(
        "notes.html",
        answer=answer,
        error=error
    )
    
# ---------------- DEMO NOTES ----------------

def get_demo_notes(subject, topic, note_type):

    return f"""
DEMO MODE - Sample Study Notes

Subject: {subject}
Topic: {topic}
Note Type: {note_type}

1. Introduction:
{topic} is an important concept in {subject}.

2. Definition:
{topic} refers to a fundamental concept studied
in the subject of {subject}.

3. Important Points:
- Understand the basic concept.
- Study its features and working.
- Learn its important principles.
- Understand its practical applications.

4. Examples:
Refer to practical examples related to {topic}.

5. Advantages:
- Improves subject understanding.
- Helps in examination preparation.
- Builds technical knowledge.

6. Conclusion:
{topic} is useful for understanding important
concepts in {subject}.

Note: This is a sample Demo Mode answer.
It is not generated by Gemini AI.
"""
if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)