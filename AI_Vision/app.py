
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import plotly.graph_objects as go

from question_generator import generate_question
from question_evaluator import evaluate_answer

from database import (
    init_db,
    create_interview,
    save_question_result,
    complete_interview,
    get_completed_interviews,
    get_question_history,
)

from auth import register_user, login_user


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="AI Mock Interview",
    page_icon="🎯",
    layout="wide",
)


st.markdown("""
<style>
/* Sidebar surface */
[data-testid="stSidebar"] {
    background: #0B1020;
    border-right: 1px solid #202941;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
}

/* Brand */
.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 4px 20px;
}

.brand-icon {
    width: 44px;
    height: 44px;
    border-radius: 13px;
    background: linear-gradient(135deg, #8B5CF6, #6D28D9);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: 700;
}

.brand-name {
    color: #F8FAFC;
    font-size: 21px;
    font-weight: 750;
    letter-spacing: -0.6px;
}

.brand-subtitle {
    color: #929DB4;
    font-size: 9px;
    letter-spacing: 1.5px;
    margin-top: 4px;
}

.sidebar-divider {
    border-top: 1px solid #263047;
    margin: 4px 0 24px;
}

.sidebar-label {
    color: #8793AA;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin: 0 0 12px 8px;
}

/* Navigation */
[data-testid="stSidebar"] [data-testid="stRadio"] > label {
    display: none;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 7px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 10px;
    padding: 10px 12px;
    color: #C7D0E0;
    transition: background 0.2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #192239;
    color: #FFFFFF;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(
    input:checked
) {
    background: #292044;
    color: #DDD0FF;
    font-weight: 600;
}

/* Candidate profile */
.candidate-card {
    display: flex;
    align-items: center;
    gap: 11px;
    background: #151D30;
    border: 1px solid #29334A;
    border-radius: 12px;
    padding: 13px 11px;
    margin-top: 26px;
}

.candidate-avatar {
    width: 39px;
    height: 39px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #514078;
    color: white;
    font-weight: 700;
    font-size: 17px;
}

.candidate-name {
    color: #F8FAFC;
    font-weight: 600;
    font-size: 13px;
    overflow-wrap: anywhere;
}

.candidate-caption {
    color: #929DB4;
    font-size: 11px;
    margin-top: 3px;
}

/* Sidebar email */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #929DB4;
    font-size: 11px;
}

/* Logout button */
[data-testid="stSidebar"] .stButton button {
    border: 1px solid #34415B;
    border-radius: 9px;
    background: transparent;
    color: #D5DCEC;
    min-height: 42px;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] .stButton button:hover {
    border-color: #8B5CF6;
    color: #FFFFFF;
    background: #211A37;
}


/* Use one consistent background across the app */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"] {
    background-color: #0B1020 !important;
}

/* Sidebar matches the main page */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
    background-color: #0B1020 !important;
}

/* Hero section */
.hero-section,
.hero,
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #0B1020;
}

</style>
""", unsafe_allow_html=True)


# Initialize database tables.
init_db()


# ---------------- SESSION STATE ----------------

defaults = {
    "logged_in": False,
    "user_id": None,
    "candidate_name": "",
    "candidate_email": "",
    "current_question": "",
    "current_role": "",
    "current_skills": [],
    "current_evaluation": None,
    "current_interview_id": None,
    "interview_started_at": None,
    "question_number": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_current_interview():
    """Clear the active interview without deleting saved records."""
    st.session_state.current_question = ""
    st.session_state.current_role = ""
    st.session_state.current_skills = []
    st.session_state.current_evaluation = None
    st.session_state.current_interview_id = None
    st.session_state.interview_started_at = None
    st.session_state.question_number = 0


# ---------------- LOGIN / REGISTRATION ----------------

if not st.session_state.logged_in:
    st.title("AI Mock Interview Platform")
    st.write(
        "Practice interviews. Improve your skills. "
        "Track your progress."
    )

    st.divider()

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with login_tab:
        st.subheader("Welcome Back")

        login_email = st.text_input(
            "Email address",
            key="login_email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button("Login", type="primary"):
            if not login_email.strip() or not login_password:
                st.warning("Enter your email and password.")
            else:
                try:
                    user = login_user(
                        login_email,
                        login_password,
                    )

                    if user:
                        reset_current_interview()

                        st.session_state.user_id = user["id"]
                        st.session_state.candidate_name = user["name"]
                        st.session_state.candidate_email = user["email"]
                        st.session_state.logged_in = True

                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

                except Exception as e:
                    st.error("Login failed. Please try again.")
                    print(f"Login error: {e}")

    with register_tab:
        st.subheader("Create Your Candidate Account")

        register_name = st.text_input(
            "Full name",
            key="register_name",
        )

        register_email = st.text_input(
            "Email address",
            key="register_email",
        )

        register_password = st.text_input(
            "Create password",
            type="password",
            key="register_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="confirm_password",
        )

        st.caption(
            "Use at least 8 characters. Choose a unique password."
        )

        if st.button("Create Account", type="primary"):
            if not all([
                register_name.strip(),
                register_email.strip(),
                register_password,
                confirm_password,
            ]):
                st.warning("Please fill in all fields.")

            elif register_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                try:
                    success, message = register_user(
                        register_name,
                        register_email,
                        register_password,
                    )

                    if success:
                        st.success(
                            "Account created! Open the Login tab "
                            "and sign in with your new credentials."
                        )
                    else:
                        st.error(message)

                except Exception as e:
                    st.error(
                        "Registration failed. Please try again."
                    )
                    print(f"Registration error: {e}")

    st.stop()

# ---------------- CUSTOM SIDEBAR ----------------


# Apply pending navigation before creating the radio widget.
if "navigate_to" in st.session_state:
    st.session_state["main_navigation"] = (
        st.session_state.pop("navigate_to")
    )

with st.sidebar:
    st.markdown("""
        <div class="brand">
            <div class="brand-icon">◎</div>
            <div>
                <div class="brand-name">PrepOrbit</div>
                <div class="brand-subtitle">AI INTERVIEW STUDIO</div>
            </div>
        </div>
        <div class="sidebar-divider"></div>
        <div class="sidebar-label">WORKSPACE</div>
    """, unsafe_allow_html=True)

    
    
    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Start Interview",
            "Interview History",
            "Final Interview Report",
        ],
        key="main_navigation",
        label_visibility="collapsed",
    )



    st.markdown(f"""
        <div class="candidate-card">
            <div class="candidate-avatar">
                {st.session_state.candidate_name[:1].upper()}
            </div>
            <div class="candidate-details">
                <div class="candidate-name">
                    {st.session_state.candidate_name}
                </div>
                <div class="candidate-caption">
                    Candidate account
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.caption(st.session_state.candidate_email)

    if st.button("↪  Log out", use_container_width=True):
        reset_current_interview()
        st.session_state.user_id = None
        st.session_state.candidate_name = ""
        st.session_state.candidate_email = ""
        st.session_state.logged_in = False
        st.rerun()



# ---------------- DASHBOARD ----------------

if page == "Dashboard":
    st.title("Your Dashboard")

    st.write(
        f"Welcome back, {st.session_state.candidate_name}!"
    )

    try:
        # Fetch only the logged-in candidate's records.
        history = get_question_history(
            st.session_state.user_id
        )
        interviews = get_completed_interviews(
            st.session_state.user_id
        )

        total_interviews = len(interviews)
        total_questions = len(history)

        scores = [
            float(item["score"])
            for item in history
            if item.get("score") is not None
        ]

        average = (
            sum(scores) / len(scores)
            if scores else 0
        )
        best = max(scores) if scores else 0

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Interviews Completed",
            total_interviews,
        )
        col2.metric(
            "Questions Evaluated",
            total_questions,
        )
        col3.metric(
            "Average Score",
            f"{average:.1f}/10",
        )
        col4.metric(
            "Best Score",
            f"{best:g}/10",
        )

        st.divider()
        st.subheader("Your Performance")

        if history:
            df = pd.DataFrame(history)

            if "created_at" in df.columns and "score" in df.columns:
                chart_df = df[["created_at", "score"]].copy()
                chart_df["score"] = pd.to_numeric(
                    chart_df["score"],
                    errors="coerce",
                )
                chart_df = chart_df.dropna(subset=["score"])

                if not chart_df.empty:
                    st.line_chart(
                        chart_df.set_index("created_at")["score"]
                    )

            st.subheader("Recent Question Results")

            display_columns = [
                column
                for column in ["created_at", "role", "score"]
                if column in df.columns
            ]

            if display_columns:
                st.dataframe(
                    df[display_columns].head(10),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info(
                "No evaluated questions yet. Complete your first "
                "interview to see your analytics."
            )

        if interviews:
            st.divider()
            st.subheader("Completed Interviews")

            interview_df = pd.DataFrame(interviews)

            display_columns = [
                column
                for column in [
                    "started_at",
                    "completed_at",
                    "role",
                    "question_count",
                    "average_score",
                    "best_score",
                ]
                if column in interview_df.columns
            ]

            st.dataframe(
                interview_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:
        st.error("Could not load your dashboard.")
        print(f"Dashboard error: {e}")


# ---------------- INTERVIEW WORKSPACE ----------------


elif page == "Start Interview":
    st.title("Start a Mock Interview")

    interview_active = (
        st.session_state.current_interview_id is not None
    )

    if interview_active:
        st.info(
            "You have an interview in progress. Finish it before "
            "starting another one."
        )

    role_options = [
        "Java Developer",
        "Python Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Data Analyst",
    ]

    experience_options = [
        "Fresher",
        "0-1 years",
        "1-2 years",
        "2+ years",
    ]

    difficulty_options = ["Easy", "Medium", "Hard"]

    question_type_options = [
        "Technical",
        "Conceptual",
        "Situational",
        "Coding",
    ]

    role = st.selectbox(
        "Target role",
        role_options,
        disabled=interview_active,
    )

    skills_input = st.text_input(
        "Skills, separated by commas",
        placeholder="Java, Spring Boot, SQL",
        disabled=interview_active,
    )

    experience = st.selectbox(
        "Experience",
        experience_options,
        disabled=interview_active,
    )

    difficulty = st.selectbox(
        "Difficulty",
        difficulty_options,
        disabled=interview_active,
    )

    question_type = st.selectbox(
        "Question type",
        question_type_options,
        disabled=interview_active,
    )

    if st.button(
        "Generate Question",
        type="primary",
        disabled=interview_active,
    ):
        skills = [
            skill.strip()
            for skill in skills_input.split(",")
            if skill.strip()
        ]

        if not skills:
            st.warning("Enter at least one skill.")

        elif st.session_state.user_id is None:
            st.error("Your login session is invalid. Please log in again.")

        else:
            try:
                # Step 1: Generate the first question.
                with st.spinner(
                    "Generating a personalized question..."
                ):
                    question = generate_question(
                        role,
                        skills,
                        experience,
                        difficulty,
                        question_type,
                    )

                if not question:
                    st.error("No question was returned by the generator.")

                else:
                    # Step 2: Create the interview in the database.
                    interview_id = str(uuid.uuid4())

                    create_interview(
                        interview_id,
                        st.session_state.user_id,
                        role,
                        skills,
                        experience,
                        difficulty,
                        question_type,
                    )

                    # Step 3: Save the active interview in session state.
                    st.session_state.current_interview_id = interview_id
                    st.session_state.interview_started_at = datetime.now()
                    st.session_state.question_number = 1
                    st.session_state.current_question = question
                    st.session_state.current_role = role
                    st.session_state.current_skills = skills
                    st.session_state.current_evaluation = None

                    st.rerun()

            except Exception as e:
                st.error(
                    f"Interview start error: {type(e).__name__}: {e}"
                )
                st.exception(e)
                print(f"Interview start error: {e}")

    question = st.session_state.current_question

    if question:
        st.divider()

        st.subheader(
            f"Question {st.session_state.question_number}"
        )
        st.info(question)

        answer = st.text_area(
            "Your answer",
            height=180,
            key=(
                f"candidate_answer_"
                f"{st.session_state.current_interview_id}_"
                f"{st.session_state.question_number}"
            ),
            disabled=(
                st.session_state.current_evaluation is not None
            ),
        )

        # Evaluate the current question only once.
        if st.session_state.current_evaluation is None:
            if st.button("Evaluate Answer", type="primary"):
                if not answer.strip():
                    st.warning("Please enter an answer.")

                else:
                    try:
                        with st.spinner("Evaluating your answer..."):
                            result = evaluate_answer(
                                question,
                                answer,
                            )

                        if result is None:
                            st.error(
                                "Evaluation failed or returned "
                                "invalid data. Please try again."
                            )

                        else:
                            save_question_result(
                                st.session_state.current_interview_id,
                                st.session_state.question_number,
                                question,
                                answer,
                                result,
                            )

                            st.session_state.current_evaluation = result
                            st.rerun()

                    except Exception as e:
                        st.error(
                            f"Evaluation/save error: "
                            f"{type(e).__name__}: {e}"
                        )
                        st.exception(e)
                        print(f"Evaluation/save error: {e}")

        result = st.session_state.current_evaluation

        if result is not None:
            st.subheader("Your Evaluation")

            st.metric("Score", f"{result['score']}/10")
            st.write("**Feedback:**", result["feedback"])

            st.write("**Strengths**")
            for item in result.get("strengths", []):
                st.markdown(f"- {item}")

            st.write("**Areas to Improve**")
            for item in result.get("weaknesses", []):
                st.markdown(f"- {item}")

            st.write("**Suggestion:**", result["suggestion"])

            st.divider()

            col_next, col_finish = st.columns(2)

            with col_next:
                if st.button("Next Question", type="primary"):
                    try:
                        with st.spinner(
                            "Adapting your next question..."
                        ):
                            next_question = generate_question(
                                role=st.session_state.current_role,
                                skills=st.session_state.current_skills,
                                experience=experience,
                                difficulty=difficulty,
                                question_type=question_type,
                                previous_evaluation=result,
                                previous_question=question,
                            )

                        if next_question:
                            st.session_state.current_question = next_question
                            st.session_state.current_evaluation = None
                            st.session_state.question_number += 1
                            st.rerun()
                        else:
                            st.error("No question was returned.")

                    except Exception as e:
                        st.error(
                            f"Next question error: {type(e).__name__}: {e}"
                        )
                        st.exception(e)
                        print(f"Next question error: {e}")

            
            
            with col_finish:
                if st.button("Finish Interview", type="primary"):
                    try:
                        interview_id = st.session_state.current_interview_id

                        completed = complete_interview(
                            interview_id,
                            st.session_state.user_id,
                        )

                        if completed:
                            # Preserve the destination for the next app run.
                            st.session_state["navigate_to"] = (
                                "Final Interview Report"
                            )

                            # Clear the active interview.
                            reset_current_interview()

                            # Rerun the app.
                            st.rerun()

                        else:
                            st.warning(
                                "Could not complete the interview. "
                                "Please try again."
                            )

                    except Exception as e:
                        st.error(
                            f"Finish interview error: {type(e).__name__}: {e}"
                        )
                        st.exception(e)


                        print(f"Finish interview error: {e}")


# ---------------- INTERVIEW HISTORY ----------------

elif page == "Interview History":
    st.title("Your Interview History")

    try:
        history = get_question_history(
            st.session_state.user_id
        )

        interviews = get_completed_interviews(
            st.session_state.user_id
        )

        # Show question-by-question history.
        if not history:
            st.info(
                "You haven't evaluated any interview questions yet."
            )

        else:
            st.subheader("Question-by-Question Results")

            for item in reversed(history):
                with st.expander(
                    f"{item.get('role', 'Interview')} | "
                    f"Question {item.get('question_number', '?')} | "
                    f"Score: {item.get('score', 'N/A')}/10"
                ):
                    st.write(
                        "**Date:**",
                        item.get("created_at", "Not available"),
                    )

                    st.write(
                        "**Skills:**",
                        ", ".join(item.get("skills") or []),
                    )

                    st.write(
                        "**Question:**",
                        item.get("question_text", ""),
                    )

                    st.write(
                        "**Your Answer:**",
                        item.get("answer_text", ""),
                    )

                    st.write(
                        "**Feedback:**",
                        item.get("feedback", ""),
                    )

                    st.write("**Strengths**")
                    for strength in item.get("strengths") or []:
                        st.markdown(f"- {strength}")

                    st.write("**Weaknesses**")
                    for weakness in item.get("weaknesses") or []:
                        st.markdown(f"- {weakness}")

                    st.write(
                        "**Suggestion:**",
                        item.get("suggestion", ""),
                    )

        # Show completed interview summaries.
        st.divider()
        st.subheader("Completed Interview Summary")

        if interviews:
            interview_df = pd.DataFrame(interviews)

            display_columns = [
                column
                for column in [
                    "started_at",
                    "completed_at",
                    "role",
                    "question_count",
                    "average_score",
                    "best_score",
                ]
                if column in interview_df.columns
            ]

            if display_columns:
                st.dataframe(
                    interview_df[display_columns],
                    use_container_width=True,
                    hide_index=True,
                )

            # Compare average scores across completed interviews.
            if (
                "started_at" in interview_df.columns
                and "average_score" in interview_df.columns
            ):
                chart_df = interview_df[
                    ["started_at", "average_score"]
                ].copy()

                chart_df["average_score"] = pd.to_numeric(
                    chart_df["average_score"],
                    errors="coerce",
                )

                chart_df = chart_df.dropna(
                    subset=["average_score"]
                )

                if not chart_df.empty:
                    st.subheader("Score Comparison")

                    st.bar_chart(
                        chart_df.set_index("started_at")[
                            "average_score"
                        ]
                    )

        else:
            st.info(
                "No completed interviews yet. Finish an interview "
                "to see its summary here."
            )

    except Exception as e:
        st.error("Could not load your interview history.")
        st.exception(e)
        print(f"History error: {e}")

        

elif page == "Final Interview Report":
    st.title("📊 Final Interview Report")
    st.write(
        "Review your performance, identify your strengths, "
        "and discover what to practice next."
    )

    try:
        # --------------------------------------------------
        # 1. Fetch interview history
        # --------------------------------------------------
        history = get_question_history(st.session_state.user_id)
        interviews = get_completed_interviews(st.session_state.user_id)

        if not interviews:
            st.info(
                "No completed interviews yet. Complete an interview "
                "to generate your first report."
            )

        else:
            # --------------------------------------------------
            # 2. Select a completed interview
            # --------------------------------------------------
            selected_interview = st.selectbox(
                "Choose a completed interview",
                options=interviews,
                format_func=lambda item: (
                    f"{item.get('role', 'Interview')} | "
                    f"{item.get('completed_at', 'Date unavailable')}"
                ),
                key="report_interview",
            )

            interview_id = selected_interview.get(
                "interview_id",
                selected_interview.get("id"),
            )

            if interview_id is None:
                st.error(
                    "Interview ID is missing. Check the data returned "
                    "by get_completed_interviews() in database.py."
                )

            else:
                # --------------------------------------------------
                # 3. Filter results for the selected interview
                # --------------------------------------------------
                results = [
                    item for item in history
                    if str(item.get("interview_id")) == str(interview_id)
                ]

                scored_results = []

                for item in results:
                    try:
                        score = float(item["score"])

                        if 0 <= score <= 10:
                            scored_results.append((item, score))

                    except (KeyError, TypeError, ValueError):
                        continue

                # Sort questions numerically
                def question_sort_key(result):
                    item, _ = result
                    try:
                        return int(item.get("question_number", 0))
                    except (TypeError, ValueError):
                        return 0

                scored_results.sort(key=question_sort_key)

                if not scored_results:
                    st.warning(
                        "No valid saved question evaluations were found "
                        "for this interview."
                    )

                else:
                    # --------------------------------------------------
                    # 4. Calculate performance statistics
                    # --------------------------------------------------
                    scores = [score for _, score in scored_results]

                    average_score = sum(scores) / len(scores)
                    best_score = max(scores)
                    lowest_score = min(scores)

                    st.subheader("Overall Performance")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Average Score",
                        f"{average_score:.1f}/10",
                    )
                    col2.metric(
                        "Best Score",
                        f"{best_score:.1f}/10",
                    )
                    col3.metric(
                        "Lowest Score",
                        f"{lowest_score:.1f}/10",
                    )
                    col4.metric(
                        "Questions Evaluated",
                        len(scores),
                    )

                    st.progress(
                        min(max(average_score / 10, 0.0), 1.0)
                    )

                    # --------------------------------------------------
                    # 5. Question-wise performance chart
                    # --------------------------------------------------
                    st.divider()
                    st.subheader("Question-wise Performance")

                    chart_data = pd.DataFrame([
                        {
                            "Question": (
                                f"Q{item.get('question_number', index + 1)}"
                            ),
                            "Score": score,
                        }
                        for index, (item, score)
                        in enumerate(scored_results)
                    ])

                    # Ensure numeric data and remove invalid rows
                    chart_data["Score"] = pd.to_numeric(
                        chart_data["Score"],
                        errors="coerce",
                    )
                    chart_data = chart_data.dropna(subset=["Score"])

                    if chart_data.empty:
                        st.warning("There are no valid scores to plot.")

                    elif (chart_data["Score"] == 0).all():
                        st.warning(
                            "All saved scores for this interview are 0/10. "
                            "The chart has no positive-height bars because "
                            "the stored scores are zero. Check the saved "
                            "evaluations and score extraction in your "
                            "evaluator/database code."
                        )

                        # Show the actual data instead of hiding the issue.
                        st.dataframe(
                            chart_data,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:
                        fig = go.Figure()

                        fig.add_trace(
                            go.Bar(
                                x=chart_data["Question"],
                                y=chart_data["Score"],
                                text=[
                                    f"{score:.1f}/10"
                                    for score in chart_data["Score"]
                                ],
                                textposition="outside",
                                marker=dict(
                                    color="#8B5CF6",
                                    line=dict(
                                        color="#A78BFA",
                                        width=1,
                                    ),
                                ),
                                hovertemplate=(
                                    "<b>%{x}</b><br>"
                                    "Score: %{y:.1f}/10"
                                    "<extra></extra>"
                                ),
                                cliponaxis=False,
                            )
                        )

                        fig.update_layout(
                            title="Score for Each Interview Question",
                            xaxis_title="Interview Question",
                            yaxis_title="Score out of 10",
                            yaxis=dict(
                                range=[0, 11.5],
                                tickmode="linear",
                                tick0=0,
                                dtick=2,
                                fixedrange=True,
                                showgrid=True,
                                gridcolor="rgba(150,150,150,0.2)",
                            ),
                            xaxis=dict(
                                type="category",
                                categoryorder="array",
                                categoryarray=chart_data["Question"].tolist(),
                            ),
                            height=430,
                            margin=dict(
                                l=45,
                                r=25,
                                t=75,
                                b=65,
                            ),
                            showlegend=False,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                        )

                    # --------------------------------------------------
                    # 6. Question-by-question review
                    # --------------------------------------------------
                    st.divider()
                    st.subheader("Question Review")

                    for item, score in scored_results:
                        question_number = item.get(
                            "question_number",
                            "N/A",
                        )

                        with st.expander(
                            f"Question {question_number} | "
                            f"Score: {score:.1f}/10"
                        ):
                            st.markdown("**Question**")
                            st.write(
                                item.get("question_text")
                                or "Question text unavailable."
                            )

                            st.markdown("**Your Answer**")
                            st.write(
                                item.get("answer_text")
                                or "No answer saved."
                            )

                            st.markdown("**Feedback**")
                            st.write(
                                item.get("feedback")
                                or "No feedback recorded."
                            )

                            st.markdown("**Suggestion**")
                            st.write(
                                item.get("suggestion")
                                or "No suggestion recorded."
                            )

                    # --------------------------------------------------
                    # 7. Combine strengths and weaknesses
                    # --------------------------------------------------
                    strengths = list(dict.fromkeys(
                        strength
                        for item, _ in scored_results
                        for strength in (item.get("strengths") or [])
                        if isinstance(strength, str) and strength.strip()
                    ))

                    weaknesses = list(dict.fromkeys(
                        weakness
                        for item, _ in scored_results
                        for weakness in (item.get("weaknesses") or [])
                        if isinstance(weakness, str) and weakness.strip()
                    ))

                    left, right = st.columns(2)

                    with left:
                        st.subheader("💪 Your Strengths")

                        if strengths:
                            for strength in strengths:
                                st.markdown(f"- {strength}")
                        else:
                            st.info("No strengths recorded.")

                    with right:
                        st.subheader("🎯 Areas to Improve")

                        if weaknesses:
                            for weakness in weaknesses:
                                st.markdown(f"- {weakness}")
                        else:
                            st.info("No improvement areas recorded.")

                    # --------------------------------------------------
                    # 8. Personalized improvement plan
                    # --------------------------------------------------
                    st.divider()
                    st.subheader("🚀 Your Improvement Plan")

                    if average_score < 5:
                        st.write(
                            "Focus on fundamentals. Review core concepts, "
                            "practise explaining them clearly, and use "
                            "small examples to demonstrate understanding."
                        )

                    elif average_score < 8:
                        st.write(
                            "Focus on consistency. Structure answers, "
                            "explain your reasoning, and include practical "
                            "examples to support your points."
                        )

                    else:
                        st.write(
                            "Great progress. Practise advanced scenarios, "
                            "debugging, trade-offs, and comparisons between "
                            "alternative solutions."
                        )

                    if weaknesses:
                        st.markdown("**Recommended practice priorities**")

                        for weakness in weaknesses:
                            st.markdown(f"- Practise: {weakness}")

                    st.caption(
                        "This report uses saved evaluations. It does not "
                        "make another LLM API call."
                    )

    except Exception as e:
        st.error("Could not generate the final interview report.")
        print(f"Final report error: {e}")
