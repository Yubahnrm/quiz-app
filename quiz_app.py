import streamlit as st
from groq import Groq
import re
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ──
st.set_page_config(
    page_title="🎓 Smart Quiz App",
    page_icon="🎓",
    layout="centered"
)

# ── Custom Style ──
st.markdown("""
    <style>
    .title { text-align: center; color: #2c3e50; font-size: 2.5em; font-weight: bold; }
    .subtitle { text-align: center; color: #7f8c8d; font-size: 1.2em; }
    .question-box { background: white; padding: 20px; border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px 0; }
    .score-box { background: linear-gradient(135deg, #667eea, #764ba2);
                 padding: 30px; border-radius: 20px; color: white; text-align: center; }
    .motivate { background: #fff9c4; padding: 15px; border-radius: 10px;
                color: #f39c12; font-size: 1.1em; text-align: center; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# ── Session State ──
def init_state():
    defaults = {
        "page": "home",
        "questions": [],
        "current_q": 0,
        "score": 0,
        "answers": [],
        "start_time": None,
        "name": "",
        "topic": "",
        "feedback": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Get API Key ──
def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found. Please add it in Streamlit secrets.")
        st.stop()
    return Groq(api_key=api_key)

# ── Generate Quiz ──
def generate_quiz(topic, num_questions, language, difficulty, quiz_type):
    client = get_client()
    prompt = f"""Create {num_questions} {quiz_type} questions about {topic} in {language} language.
The difficulty level should be {difficulty}.
For each question provide:
1. The question
2. The options (if MCQ or True/False)
3. The correct answer
4. A brief explanation of why that answer is correct.

Format exactly like this:
Q1: [question]
A) [option]
B) [option]
C) [option]
D) [option]
Correct Answer: [answer]
Explanation: [why this is correct]

Q2: [question]
...and so on."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000
    )
    return response.choices[0].message.content

# ── Parse Questions ──
def parse_questions(quiz_text):
    questions = re.split(r'Q[0-9]+:', quiz_text)
    questions = [q.strip() for q in questions if q.strip()]
    parsed = []
    for q in questions:
        lines = q.strip().split("\n")
        lines = [l.strip() for l in lines if l.strip()]
        correct_answer = ""
        explanation = ""
        question_lines = []
        for line in lines:
            if line.lower().startswith("correct answer:"):
                correct_answer = line.split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()
            else:
                question_lines.append(line)
        parsed.append({
            "question": question_lines,
            "correct": correct_answer,
            "explanation": explanation
        })
    return parsed

# ── Motivation ──
def get_motivation(percentage, name):
    if percentage == 100:
        return f"🌟 {name}, PERFECT score! You are absolutely BRILLIANT!"
    elif percentage >= 80:
        return f"🎉 Amazing work {name}! You are a star learner! Keep shining!"
    elif percentage >= 60:
        return f"👍 Well done {name}! You are on the right path! Keep going!"
    elif percentage >= 40:
        return f"💪 Keep going {name}! Every expert was once a beginner!"
    else:
        return f"🌱 {name}, the fact that you tried makes you a winner! Never stop exploring!"

# ════════════════════════════════
# PAGE 1 — HOME
# ════════════════════════════════
if st.session_state.page == "home":
    st.markdown('<p class="title">🎓 Smart Quiz App</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Learn • Explore • Grow</p>', unsafe_allow_html=True)
    st.markdown("---")

    name = st.text_input("👤 Your Name", placeholder="Enter your name...")
    topic = st.text_input("📚 Quiz Topic", placeholder="e.g. Basic Accounting, Science, History...")

    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.selectbox("🔢 Number of Questions", [5, 10, 15, 20])
        difficulty = st.selectbox("⚡ Difficulty", ["Easy", "Medium", "Hard"])
    with col2:
        language = st.selectbox("🌍 Language", ["English", "Nepali", "Hindi", "Spanish", "French"])
        quiz_type = st.selectbox("📝 Quiz Type", ["MCQ", "True/False", "Short Answer", "Fill in the Blank"])

    st.markdown("---")

    if st.button("🚀 Generate My Quiz!", use_container_width=True):
        if not name:
            st.warning("⚠️ Please enter your name!")
        elif not topic:
            st.warning("⚠️ Please enter a topic!")
        else:
            with st.spinner("🧠 Creating your quiz... please wait..."):
                quiz_text = generate_quiz(topic, num_questions, language, difficulty, quiz_type)
                st.session_state.questions = parse_questions(quiz_text)
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.answers = []
                st.session_state.name = name
                st.session_state.topic = topic
                st.session_state.start_time = time.time()
                st.session_state.feedback = None
                st.session_state.page = "quiz"
                st.rerun()

# ════════════════════════════════
# PAGE 2 — QUIZ
# ════════════════════════════════
elif st.session_state.page == "quiz":
    questions = st.session_state.questions
    current = st.session_state.current_q
    total = len(questions)

    if current >= total:
        st.session_state.page = "results"
        st.rerun()

    else:
        st.markdown(f"### 👋 Hello, {st.session_state.name}!")
        st.markdown(f"📚 Topic: **{st.session_state.topic}**")

        st.progress(current / total)
        st.markdown(f"**Question {current + 1} of {total}**")

        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f"⏱️ Time elapsed: **{elapsed} seconds**")

        q = questions[current]

        if st.session_state.feedback:
            fb = st.session_state.feedback
            if fb["is_correct"]:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong! Correct Answer: {fb['correct']}")
            st.info(f"💡 Explanation: {fb['explanation']}")
            if st.button("➡️ Next Question", use_container_width=True):
                st.session_state.feedback = None
                st.rerun()

        else:
            st.markdown('<div class="question-box">', unsafe_allow_html=True)
            for line in q["question"]:
                st.markdown(f"**{line}**")
            st.markdown('</div>', unsafe_allow_html=True)

            answer = st.text_input("✏️ Your Answer:", key=f"answer_{current}")

            if st.button("✅ Submit Answer", use_container_width=True):
                correct = q["correct"]
                is_correct = answer.strip().lower() in correct.lower()

                if is_correct:
                    st.session_state.score += 1

                st.session_state.answers.append({
                    "question": q["question"],
                    "your_answer": answer,
                    "correct": correct,
                    "explanation": q["explanation"],
                    "is_correct": is_correct
                })

                st.session_state.feedback = {
                    "is_correct": is_correct,
                    "correct": correct,
                    "explanation": q["explanation"]
                }
                st.session_state.current_q += 1
                st.rerun()

# ════════════════════════════════
# PAGE 3 — RESULTS
# ════════════════════════════════
elif st.session_state.page == "results":
    name = st.session_state.name
    score = st.session_state.score
    total = len(st.session_state.questions)
    percentage = (score / total) * 100 if total > 0 else 0

    st.markdown('<div class="score-box">', unsafe_allow_html=True)
    st.markdown(f"## 🏆 Quiz Complete, {name}!")
    st.markdown(f"### Score: {score} / {total}")
    st.markdown(f"### Percentage: {percentage:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="motivate">{get_motivation(percentage, name)}</div>',
                unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Your Answer Review:")
    for i, ans in enumerate(st.session_state.answers):
        icon = "✅" if ans["is_correct"] else "❌"
        with st.expander(f"{icon} Question {i+1}"):
            for line in ans["question"]:
                st.write(line)
            st.write(f"**Your Answer:** {ans['your_answer']}")
            st.write(f"**Correct Answer:** {ans['correct']}")
            st.write(f"**💡 Explanation:** {ans['explanation']}")

    result_text = f"Quiz Results - {name}\nTopic: {st.session_state.topic}\nScore: {score}/{total} ({percentage:.1f}%)\n\n"
    for i, ans in enumerate(st.session_state.answers):
        result_text += f"Q{i+1}: {' '.join(ans['question'])}\n"
        result_text += f"Your Answer: {ans['your_answer']}\n"
        result_text += f"Correct: {ans['correct']}\n"
        result_text += f"Explanation: {ans['explanation']}\n\n"

    st.download_button("📥 Download My Results", result_text,
                       file_name=f"{name}_quiz_results.txt", use_container_width=True)

    if st.button("🔄 Take Another Quiz", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
