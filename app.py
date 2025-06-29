import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64
import os
from dotenv import load_dotenv
import pandas as pd
import zipfile
import numpy as np
from streamlit_option_menu import option_menu 
import requests
import datetime as dt
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google_sheet_logger import connect_to_google_sheet, append_row_to_sheet, append_to_google_sheet


from dotenv import load_dotenv


sheet="https://docs.google.com/spreadsheets/d/1z8Pt4YHQEmMx_HHcya0BSOSFFY2N7TZOxaTkriCYP7I/edit?usp=sharing"


columns = [
    "faculty", "department", "subject", "date_time", "topic", "observer", "position",
    "mean_skills", "mean_relationship", "mean_mastery", "mean_management", "overall_mean",
    "scores_skills", "scores_relationship", "scores_mastery", "scores_management"
]


default_drive_url = st.query_params.get("drive", "")
default_date=dt.datetime.now().date()
default_time=dt.datetime.now().strftime("%H:%M:%S")
# === Sidebar Navigation ===
with st.sidebar:
    selected = option_menu(
        "Navigation",
        ["Evaluation Form", "Documentation", "Feedback"],
        icons=["clipboard-check", "book", "chat-dots"],
        menu_icon="cast",
        default_index=0
    )

if selected == "Documentation":
    st.title("📘 Project Documentation")

    st.markdown("**📝  Classroom Visitation Evaluation Form Generator**")
    st.markdown("By: Dr. Al Rey Villagracia")
    st.markdown(" ")
    st.markdown("### 🎯 Objectives")
    st.markdown("""
    - Digitize and streamline faculty evaluation.
    - Automatically generate standardized PDF reports.
    - Support bulk generation of evaluations via Excel/CSV.
    - Allow downloading of ZIP with multiple PDFs.
    """)

    st.markdown("### 🛠 How to Use")
    st.markdown("""
    1. Go to the **Evaluation Form** tab.
    2. Enter faculty information and rate each area using the dropdowns.
    3. You can also upload a CSV/Excel file with multiple evaluations.
    4. Click **Generate PDF** to download one file, or all in ZIP if multiple entries.

    ### 🔗 Example URL to Auto-Load Google Drive File
    Pass a `?drive=` parameter in the app URL:

    ```
    https://class-eval.streamlit.app/?drive=https://drive.google.com/file/d/1ABCDefGhIJKLmnopQRStuvW/view
    ```

    (Make sure the file is shared publicly with "Anyone with the link")
    
    """)


    
    st.markdown("### 📂 Templates & Links")
    st.markdown("""
    - 📥 [Evaluation CSV Template](https://drive.google.com/file/d/1BQETBQg6nBht5M_wDlLVlanqUREeJsvn/view?usp=sharing)
    - 📄 [Word Document Format](https://docs.google.com/document/d/1z3QMqGd9n6s2g4deZLY-dRPK7p7SdONs/edit?usp=sharing&ouid=107363987308890013179&rtpof=true&sd=true)       
    """)

    st.markdown("### 🧾 Template Legend")
    st.markdown("""
        The uploaded CSV/Excel file should have the following column headers:
    
        - `faculty`: Name of Faculty
        - `department`: Department name
        - `subject`: Subject or Course Title
        - `date_time`: Date and time of observation
        - `topic`: Subject matter under discussion
        - `observer`: Evaluator's name
        - `position`: Evaluator's position
    
        Ratings for the 4 categories:
        - `q1` to `q21`: Numeric scores (1–5) corresponding to each question in order.
    
        🔢 Questions are in order as:
        1–6: Teaching Skills  
        7–11: Teacher-Student Relationship  
        12–16: Mastery of Subject Matter  
        17–21: Classroom Management
        """)        
    

load_dotenv()
def extract_file_id(drive_url):
    if "id=" in drive_url:
        return drive_url.split("id=")[-1].split("&")[0]
    elif "/d/" in drive_url:
        return drive_url.split("/d/")[1].split("/")[0]
    return None

def load_drive_file_as_dataframe(url):
    file_id = extract_file_id(url)
    if not file_id:
        st.warning("⚠️ Invalid Google Drive link.")
        return None
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(download_url)
        response.raise_for_status()
        data = BytesIO(response.content)
        try:
            return pd.read_csv(data)
        except:
            data.seek(0)
            return pd.read_excel(data)
    except Exception as e:
        st.error(f"❌ Error loading file from Drive: {e}")
        return None

def load_uploaded_file(upload_file):
    try:
        if upload_file.name.endswith(".csv"):
            return pd.read_csv(upload_file)
        else:
            return pd.read_excel(upload_file)
    except Exception as e:
        st.error(f"❌ Error loading uploaded file: {e}")
        return None
        
def generate_filled_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 40, "CLASSROOM VISITATION")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 60, "(PEER/CHAIR EVALUATION FORM)")

   
    c.setFont("Helvetica", 12)
    global y
    y = height - 90
    line_spacing = 13

    def draw_line(text, indent=50):
        global y
        c.setFont("Helvetica", 9)
        c.drawString(indent, y, text)
        # Calculate underline based on text width
        text_width = c.stringWidth(text, "Helvetica", 9)
        underline_y = y - 1
        #c.line(indent, underline_y, indent + text_width, underline_y)
        y -= line_spacing

    def draw_partial_underline(label, value, x_start, y, font="Helvetica", size=9,padding=5,underline_gap=100,order=True):
        c.setFont(font, size)
        if order: c.drawString(x_start, y, label)
        label_width = c.stringWidth(label, font, size)
        value_x = x_start + label_width + 5
        padded_value = value + "      "  # add a few trailing spaces for clearer underline
        c.drawString(value_x, y, padded_value)
        value_width = c.stringWidth(value, font, size)
        underline_y = y - 1
        c.line(value_x, underline_y, underline_gap , underline_y)
        if not(order): c.drawString(x_start, y, label)
        return y - line_spacing  # 🔁 Return updated y value!

    def draw_partial_underline2(label, value, x_start, y, font="Helvetica", size=9,padding=5,underline_gap=100,order=True):
        c.setFont(font, size)      
        
        value_x = x_start 
        c.drawString(value_x, y, value)
        value_width = c.stringWidth(value, font, size)
        underline_y = y - 1
        c.line(value_x, underline_y, underline_gap , underline_y)
        c.drawString(x_start+10, y, label)
        
        return y - line_spacing  # 🔁 Return updated y value!

    c.setFont("Helvetica", 9)
    y = draw_partial_underline("Name of Faculty: ", data['faculty'], 50, y,underline_gap=340) + line_spacing
    y = draw_partial_underline("Department: ", data['department'], 350, y,underline_gap=550) 
    y = draw_partial_underline("Subject: ", data['subject'], 50, y,underline_gap=340)+ line_spacing 
    y = draw_partial_underline("Date/Time of Observation: ", data['date_time'], 350, y,underline_gap=550) 
    y = draw_partial_underline("Subject Matter Under Discussion: ", data['topic'], 50, y,underline_gap=550)
    y = draw_partial_underline("Observer’s Name: ", data['observer'], 50, y,underline_gap=340) + line_spacing
    y = draw_partial_underline("Position: ", data['position'], 350, y,underline_gap=550)
    draw_line("=================================================================================================.")
    y -= 10
    draw_line("Direction: Below are teacher behaviors/characteristics that are readily observable in class.")
    draw_line("Please rate the above faculty on each item using the scale below.")
    draw_line("                                                        5 - Very Highly Observable/Noticeable")
    draw_line("                                                        4 - Highly Observable/Noticeable")
    draw_line("                                                        3 - Moderately Observable/Noticeable")
    draw_line("                                                        2 - Slightly Observable/Noticeable")
    draw_line("                                                        1 - Not At All Observable/Noticeable")

    def draw_section(title, items, scores, mean):
        global y
        c.setFont("Helvetica-Bold", 10)
        y -= 15
        draw_line(title)
        c.setFont("Helvetica", 9)
        for i, (item, score) in enumerate(zip(items, scores), 1):
            #draw_line(f"{score}   {i}. {item}")
            text=str(i) +'.' + item
            y = draw_partial_underline2(text, str(score), 50, y,underline_gap=60, order=False) 

        y -= 5
        y = draw_partial_underline2("      AREA MEAN", str(f"{mean:.2f}"), 50, y,underline_gap=66, order=False) 
        


    draw_section("TEACHING SKILLS", data["questions"]["skills"], data["scores"]["skills"], data["means"]["skills"])
    draw_section("TEACHER-STUDENT RELATIONSHIP", data["questions"]["relationship"], data["scores"]["relationship"], data["means"]["relationship"])
    draw_section("MASTERY OF THE SUBJECT MATTER", data["questions"]["mastery"], data["scores"]["mastery"], data["means"]["mastery"])
    draw_section("CLASSROOM MANAGEMENT AND ORGANIZATION", data["questions"]["management"], data["scores"]["management"], data["means"]["management"])
    y -= 10
    y = draw_partial_underline2("      OVERALL MEAN (Σ Area Mean / 4)", str(f"{data['means']['overall']:.2f}"), 50, y,underline_gap=66, order=False) 
    #draw_line(f"{data['means']['overall']:.2f}      OVERALL MEAN (Σ Area Mean / 4) ")

    c.save()
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Classroom Evaluation Form", layout="wide")

if selected == "Evaluation Form":
    # Place your existing evaluation form code here

    st.title("Classroom Visitation Form (Peer/Chair Evaluation) PDF Generator")

    if st.button("🔄 Reset Form"):
        st.query_params.clear()  # Clear query params like ?drive=
        st.session_state.clear()  # Reset all Streamlit inputs
        st.rerun()  # Refresh the app
    
    # with open("/mount/src/applied-research-projects/16_Class_Evaluation/evaluation_template.docx", "rb") as docx_file:
    #         st.download_button(
    #             label="📄 Download Blank Evaluation Template (Word)",
    #             data=docx_file,
    #             file_name="evaluation_template.docx",
    #             mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    #             key='realfile'
    #         )
    
    
    #st.sidebar.header("📁 Upload Evaluation File (CSV/Excel)")
    #uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

    with st.sidebar:
        st.header("📂 Load Evaluation Data")
    
        uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])
        drive_url = st.text_input("Or paste a Google Drive file link", value=default_drive_url or "")
    
        st.caption("⚠️ Either upload a file or paste a public Google Drive link (not both).")
        st.button("🔄 Reset All", on_click=lambda: (st.session_state.clear()))
    selected_row = None
    df = None


    
    
    # Data Preprocessing
    flag=False
    if uploaded_file:
        #df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = load_uploaded_file(uploaded_file)
        st.success("✅ File uploaded successfully.")
        flag=True
    elif drive_url:
        df = load_drive_file_as_dataframe(drive_url)
        if df is not None:
            st.success("✅ File loaded from Google Drive.")
            flag=True
    if flag:
        try:
            faculty_list = df["faculty"].dropna().unique().tolist()
            selected_faculty = st.selectbox("Select Faculty to Evaluate", faculty_list)
            selected_row = df[df["faculty"] == selected_faculty].iloc[0]
            dt_obj = dt.datetime.strptime(selected_row["date_time"], "%m/%d/%Y %H:%M")
            formatted = dt_obj.strftime("%B %d, %Y at %I:%M %p") 
            default_date = dt_obj.date()  # e.g., datetime.date(2024, 6, 27)
            default_time = dt_obj.time()  # e.g., datetime.time(10, 30)
        except:
            st.error("Error reading file. Make sure to use the template. Double check the entries")
    
    # Display form fields
    st.subheader("Faculty Information")
    col1, col2, col3 = st.columns(3)
    
    def get_val(col):
        return selected_row[col] if selected_row is not None else ""
    
    with col1:
        faculty = st.text_input("Name of Faculty", value=get_val("faculty"))
        subject = st.text_input("Subject", value=get_val("subject"))
    
    with col2:
        department = st.text_input("Department", value=get_val("department"))
        #date_time = st.text_input("Date/Time of Observation", value=get_val("date_time"))
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            selected_date = st.date_input("Observation Date",value=default_date)
        with subcol2:
            selected_time = st.time_input("Time Start",value=default_time)
        datetimes = dt.datetime.combine(selected_date, selected_time)
        date_time = datetimes.strftime("%B %d, %Y at %I:%M %p")
    with col3:
        observer = st.text_input("Observer’s Name", value=get_val("observer"))
        position = st.text_input("Observer’s Position", value=get_val("position"))
    topic = st.text_input("Subject Matter Under Discussion", value=get_val("topic"))
    
    #st.markdown("**Legend: 5 = Very Highly Observable | 4 = Highly Observable | 3 = Moderately Observable | 2 = Slightly Observable | 1 = Not At All Observable**")
    
    # Ratings
    options = [
        "5 - Very Highly Observable",
        "4 - Highly Observable",
        "3 - Moderately Observable",
        "2 - Slightly Observable",
        "1 - Not At All Observable"
    ]
    
    def get_prefill(prefix):
        return selected_row.filter(like=f"{prefix}_").tolist() if selected_row is not None else []
        
    #topic = st.text_input("Subject Matter Under Discussion")
    st.markdown("**Legend: 5 = Very Highly Observable | 4 = Highly Observable | 3 = Moderately Observable | 2 = Slightly Observable | 1 = Not At All Observable**")
    
    def rating_section(title, questions, key_prefix, prefill_scores=[]):
        ratings = []
        with st.expander(f"{title} Evaluation"):
            for i, q in enumerate(questions, 1):
                default_score = prefill_scores[i-1] if i <= len(prefill_scores) else 5
                default_option = next((opt for opt in options if opt.startswith(str(default_score))), options[2])
                val = st.selectbox(
                    f"{i}. {q}",
                    options=options,
                    index=options.index(default_option),
                    key=f"{key_prefix}_{i}"
                )
                score = int(val[0])
                ratings.append(score)
        mean = round(sum(ratings) / len(ratings), 2)
        st.markdown(f"**{title} Mean:** {mean}")
        return mean, ratings
    
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mean1, sec1 = rating_section("Teaching Skills", [
            "Explains the lesson clearly and to the point",
            "Uses a variety of teaching techniques",
            "Communicates effectively",
            "Summarizes lessons effectively",
            "Delivers interesting lectures",
            "Asks thought-provoking questions"
        ], "skills", get_prefill("skills"))
    
    with col2:
        mean2, sec2 = rating_section("Teacher-Student Relationship", [
            "Gives constructive feedback",
            "Simplifies difficult topics",
            "Displays positive relationship",
            "Shows respect for students",
            "Appears comfortable in class"
        ], "relationship",get_prefill("relationship"))
    
    with col3:
        mean3, sec3 = rating_section("Mastery of Subject Matter", [
            "Displays comprehensive knowledge",
            "Raises relevant problems",
            "Relates subject to other topics",
            "Explains subject with depth",
            "Presents latest developments"
        ], "mastery",get_prefill("mastery"))
    
    with col4:
        mean4, sec4 = rating_section("Classroom Management and Organization", [
            "Promotes discipline and respect",
            "Presents logically structured lesson",
            "Uses class time efficiently",
            "Commands respect from students",
            "Minimizes disruptions"
        ], "management",get_prefill("management"))
    
    overall_mean = round((mean1 + mean2 + mean3 + mean4) / 4, 2)
    st.markdown(f"## 📊 Overall Mean: {overall_mean}")
    
    data = {
            "faculty": faculty,
            "department": department,
            "subject": subject,
            "date_time": date_time,
            "topic": topic,
            "observer": observer,
            "position": position,
            "questions": {
                "skills": [
                    "    Explains the lesson clearly and to the point",
                    "    Uses a variety of teaching techniques appropriate to student needs and subject matter",
                    "    Demonstrates ability to communicate effectively using appropriate, clear and understandable verbal, non-verbal, and writing skills",
                    "    Summarizes lessons effectively",
                    "    Delivers lectures/lessons in a stimulating/interesting manner",
                    "    Asks challenging/stimulating/thought-provoking questions"
                ],
                "relationship": [
                    "    Gives constructive feedback to students",
                    "    Simplifies difficult topics",
                    "    Displays positive relationship with students",
                    "    Shows respect for the students as persons",
                    "    Appears comfortable and at ease in handling the class"
                ],
                "mastery": [
                    "    Displays comprehensive/thorough knowledge of the subject matter to achieve curricular objectives",
                    "    Raises problems and issues relevant to the topic(s) of discussion",
                    "    Relates the subject matter to other related topics",
                    "    Explains the subject matter with depth",
                    "    Presents the latest developments in areas under discussion"
                ],
                "management": [
                    "    Displays effective techniques to promote self-discipline and maintain appropriate behavior (e.g., mutual respect) among the students",
                    "    Presents lesson in a clear, logical and appropriately structured format",
                    "    Utilizes class time efficiently",
                    "    Commands respect from students",
                    "    Conducts class with minimum disruptions from the students"
                ]
            },
            "scores": {
                "skills": sec1,
                "relationship": sec2,
                "mastery": sec3,
                "management": sec4
            },
            "means": {
                "skills": mean1,
                "relationship": mean2,
                "mastery": mean3,
                "management": mean4,
                "overall": overall_mean
            }
    
        }

    
    if st.button("Generate PDF"):
        pdf_buffer = generate_filled_pdf(data)
        st.download_button(
            label="📄 Download Current Evaluation (PDF)",
            data=pdf_buffer,
            file_name=faculty+"_evaluation_form.pdf",
            mime="application/pdf",
            key="single-pdf"
            )
        append_to_google_sheet("Evaluation Submissions",data)
    
    
    if df is not None:
        zip_path = "faculty_evaluations.zip"
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for i, row in df.iterrows():
                data = {
                    "faculty": row["faculty"],
                    "department": row["department"],
                    "subject": row["subject"],
                    "date_time": row["date_time"],
                    "topic": row["topic"],
                    "observer": row["observer"],
                    "position": row["position"],
                    "questions": {
                        "skills": [
                            "Explains the lesson clearly and to the point",
                            "Uses a variety of teaching techniques appropriate to student needs and subject matter",
                            "Demonstrates ability to communicate effectively using appropriate, clear and understandable verbal, non-verbal, and writing skills",
                            "Summarizes lessons effectively",
                            "Delivers lectures/lessons in a stimulating/interesting manner",
                            "Asks challenging/stimulating/thought-provoking questions"
                        ],
                        "relationship": [
                            "Gives constructive feedback to students",
                            "Simplifies difficult topics",
                            "Displays positive relationship with students",
                            "Shows respect for the students as persons",
                            "Appears comfortable and at ease in handling the class"
                        ],
                        "mastery": [
                            "Displays comprehensive/thorough knowledge of the subject matter to achieve curricular objectives",
                            "Raises problems and issues relevant to the topic(s) of discussion",
                            "Relates the subject matter to other related topics",
                            "Explains the subject matter with depth",
                            "Presents the latest developments in areas under discussion"
                        ],
                        "management": [
                            "Displays effective techniques to promote self-discipline and maintain appropriate behavior (e.g., mutual respect) among the students",
                            "Presents lesson in a clear, logical and appropriately structured format",
                            "Utilizes class time efficiently",
                            "Commands respect from students",
                            "Conducts class with minimum disruptions from the students"
                        ]
                    },
                    "scores": {
                        "skills": [row[f"skills_{j}"] for j in range(1, 7)],
                        "relationship": [row[f"relationship_{j}"] for j in range(1, 6)],
                        "mastery": [row[f"mastery_{j}"] for j in range(1, 6)],
                        "management": [row[f"management_{j}"] for j in range(1, 6)]
                    },
                    "means": {
                        "skills": round(np.mean([row[f"skills_{j}"] for j in range(1, 7)]), 2),
                        "relationship": round(np.mean([row[f"relationship_{j}"] for j in range(1, 6)]), 2),
                        "mastery": round(np.mean([row[f"mastery_{j}"] for j in range(1, 6)]), 2),
                        "management": round(np.mean([row[f"management_{j}"] for j in range(1, 6)]), 2),
                    }
                }
                data["means"]["overall"] = round(np.mean(list(data["means"].values())), 2)
                append_to_google_sheet("Evaluation Submissions",data)
                pdf_bytes = generate_filled_pdf(data).getvalue()
                filename = f"{row['faculty'].replace(' ', '_')}.pdf"
                zipf.writestr(filename, pdf_bytes)
    
        with open("faculty_evaluations.zip", "rb") as f:
            zip_bytes = f.read()
            st.download_button(
                label="📥 Download All Evaluation PDFs (ZIP)",
                data=zip_bytes,
                file_name="faculty_evaluations.zip",
                mime="application/zip",
                key="zip_download" 
                )

elif selected == "Feedback":
    st.title("💬 Feedback")

    st.markdown("I’d love to hear your feedback! Please share your suggestions or issues")
    st.markdown("Send your feedback to my email alrey.dlsu@gmail.com")
