from flask import Flask, request, render_template, redirect, url_for
import os
import fitz  # PyMuPDF for PDF extraction
from docx import Document
import spacy
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Ensures plots are saved to files instead of using a GUI
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Flask app
app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load job roles and descriptions from an Excel file
JOB_FILE = os.path.join(app.root_path, "data", "job role and skills.xlsx")
job_data = pd.read_excel(JOB_FILE)
job_data.columns = job_data.columns.str.strip()
job_descriptions = dict(zip(job_data["Job Role"], job_data["Technical Skills Needed"]))

# Utility functions
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def process_resume(resume_text, job_role):
    """Analyze the resume, identify matched and missing skills, and generate visualizations."""
    job_description = job_descriptions.get(job_role, "")
    if not job_description:
        return {"error": f"Job role '{job_role}' not found."}

    # Extract skills from the job description
    job_skills = set([skill.strip().lower() for skill in job_description.split(",") if skill.strip()])
    
    # Extract skills from the resume text
    resume_doc = nlp(resume_text)
    resume_skills = set([token.text.lower() for token in resume_doc if token.is_alpha])

    # Compare skills
    matched_skills = job_skills.intersection(resume_skills)
    missing_skills = job_skills - resume_skills

    # Visualization: Matched vs Missing Skills
    plt.figure(figsize=(6, 4))
    labels = ['Matched Skills', 'Missing Skills']
    sizes = [len(matched_skills), len(missing_skills)]
    colors = ['green', 'red']
    plt.bar(labels, sizes, color=colors)
    plt.title(f"Skill Match Analysis for {job_role}")
    plt.ylabel("Number of Skills")
    
    # Ensure unique file names for each job role
    sanitized_job_role = job_role.replace(" ", "_").replace("/", "_")
    plot_path = os.path.join("static", f"{sanitized_job_role}_skills_plot.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    plt.close()

    return {
        "job_role": job_role,
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "plot_path": plot_path
    }



def get_recommendations(resume_text):
    """Generate job recommendations from the Excel file."""
    recommendations = []

    # Iterate through job roles and calculate similarity
    for _, row in job_data.iterrows():
        job_role = row["Job Role"]
        description = row["Technical Skills Needed"]

        # Calculate cosine similarity using TF-IDF
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([resume_text, description])
        similarity_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

        # Append the job role and similarity score
        recommendations.append({"job_title": job_role, "similarity": similarity_score})
    
    # Sort by similarity (descending) and get top 3
    top_recommendations = sorted(recommendations, key=lambda x: x["similarity"], reverse=True)[:3]

    # Visualization: Bar chart for top 3 recommendations
    if top_recommendations:
        plt.figure(figsize=(8, 5))
        roles = [rec["job_title"] for rec in top_recommendations]
        scores = [rec["similarity"] * 100 for rec in top_recommendations]
        plt.bar(roles, scores, color=["blue", "green", "orange"])
        plt.title("Top Job Role Recommendations")
        plt.xlabel("Job Roles")
        plt.ylabel("Similarity (%)")
        plt.ylim(0, 100)  # Ensure the scale is 0-100%
        plot_path = os.path.join("static", "recommendations_plot.png")
        plt.savefig(plot_path)
        plt.close()
    else:
        plot_path = None

    return {"recommendations": top_recommendations, "plot_path": plot_path}


# Routes
@app.route("/")
def index():
    return render_template("index.html", job_roles=list(job_descriptions.keys()))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/feedback')
def feedback():
    # Render a feedback form or any relevant page
    return render_template('feedback.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    # Add logic to verify the user's credentials
    return redirect(url_for('index'))  # Redirect to home or dashboard after login

@app.route('/signup', methods=['POST'])
def signup_user():
    email = request.form['email']
    password = request.form['password']
    # Add logic to create a new user
    return redirect(url_for('login'))  # Redirect to login after signup


@app.route("/analyze_skills", methods=["POST"])
def analyze_skills():
    # Check if required inputs are present
    if "resume" not in request.files or "job_role" not in request.form:
        return render_template("index.html", error="Invalid input. Please upload a resume and enter a job role.")
    
    # Get inputs
    resume_file = request.files["resume"]
    job_role = request.form["job_role"]
    
    # Save the uploaded resume
    safe_filename = secure_filename(resume_file.filename)
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    resume_file.save(resume_path)
    
    # Extract text from the uploaded resume
    if resume_file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_path)
    elif resume_file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_path)
    else:
        return render_template("index.html", error="Unsupported file type. Please upload a PDF or DOCX file.")
    
    # Call the `process_resume` function
    result = process_resume(resume_text, job_role)
    
    # Debugging: Print the result to ensure correctness
    print("Result from process_resume:", result)
    
    # Render the feedback page with results
    return render_template("feedback.html", result=result, type="analyze")


@app.route("/get_recommendations", methods=["POST"])
def get_recommendations_route():
    if "resume" not in request.files:
        return redirect(url_for("index", error="Invalid input"))

    resume_file = request.files["resume"]
    safe_filename = secure_filename(resume_file.filename)
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    resume_file.save(resume_path)

    # Extract text from resume
    if resume_file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_path)
    elif resume_file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_path)
    else:
        return redirect(url_for("index", error="Unsupported file type"))

    # Generate recommendations
    result = get_recommendations(resume_text)

    # Render feedback page
    return render_template("feedback.html", result=result["recommendations"], plot_path=result["plot_path"], type="recommendations")


# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
