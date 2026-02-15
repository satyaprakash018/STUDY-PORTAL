from flask import (
    Flask, render_template, request, redirect,
    session, flash, send_file
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import gridfs
import io
import os

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key")

# Max upload size: 20 MB
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# -------------------------------------------------
# FILE VALIDATION
# -------------------------------------------------
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------------------
# MONGODB CONNECTION
# -------------------------------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["study_portal"]

users = db["users"]
materials = db["materials"]
fs = gridfs.GridFS(db)

# -------------------------------------------------
# LOGIN PAGE
# -------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = users.find_one({"email": email})

    if user and check_password_hash(user["password"], password):
        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        session["role"] = user.get("role", "user")
        return redirect("/dashboard")

    flash("Invalid Email or Password", "danger")
    return redirect("/")

# -------------------------------------------------
# REGISTER
# -------------------------------------------------
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    email = request.form["email"]
    if users.find_one({"email": email}):
        flash("Email already registered", "danger")
        return redirect("/register")

    users.insert_one({
        "name": request.form["name"],
        "email": email,
        "password": generate_password_hash(request.form["password"]),
        "college": request.form["college"],
        "branch": request.form["branch"],
        "year": request.form["year"],
        "role": "user"
    })

    flash("Registration successful! Please login.", "success")
    return redirect("/")

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    # Separate counts
    total_question_papers = materials.count_documents({
        "category": "question_paper"
    })

    total_study_materials = materials.count_documents({
        "category": "study_material"
    })

    # Recently uploaded (latest 5 of both)
    recent_materials = list(
        materials.find()
        .sort("_id", -1)
        .limit(5)
    )

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        total_question_papers=total_question_papers,
        total_study_materials=total_study_materials,
        recent_materials=recent_materials
    )

# -------------------------------------------------
# STUDY MATERIALS (PAGINATED)
# -------------------------------------------------
@app.route("/materials")
def materials_page():
    if "user_id" not in session:
        return redirect("/")

    page = int(request.args.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    search_query = request.args.get("q")
    selected_subject = request.args.get("subject")

    query = {"category": "study_material"}

    if search_query:
        query["$or"] = [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"subject": {"$regex": search_query, "$options": "i"}}
        ]

    if selected_subject and selected_subject != "All":
        query["subject"] = selected_subject

    total_materials = materials.count_documents(query)

    all_materials = list(
        materials.find(query)
        .skip(skip)
        .limit(per_page)
    )

    total_pages = (total_materials + per_page - 1) // per_page
    subjects = materials.distinct("subject", {"category": "study_material"})

    return render_template(
        "materials.html",
        materials=all_materials,
        subjects=subjects,
        search_query=search_query,
        selected_subject=selected_subject,
        page=page,
        total_pages=total_pages
    )

# -------------------------------------------------
# QUESTION PAPERS (TABLE FORMAT)
# -------------------------------------------------
@app.route("/question-papers")
def question_papers():
    if "user_id" not in session:
        return redirect("/")

    subject = request.args.get("subject")
    year = request.args.get("year")
    paper_type = request.args.get("paper_type")

    query = {"category": "question_paper"}

    if subject and subject != "All":
        query["subject"] = subject

    if year and year != "All":
        query["year"] = year

    if paper_type and paper_type != "All":
        query["paper_type"] = paper_type

    papers = list(materials.find(query).sort("year", -1))

    subjects = materials.distinct("subject", {"category": "question_paper"})
    years = materials.distinct("year", {"category": "question_paper"})

    return render_template(
        "question_papers.html",
        papers=papers,
        subjects=subjects,
        years=years
    )

# -------------------------------------------------
# SERVE PDF + DOWNLOAD COUNTER
# -------------------------------------------------
@app.route("/material/<file_id>")
def serve_pdf(file_id):
    if "user_id" not in session:
        return redirect("/")

    materials.update_one(
        {"file_id": ObjectId(file_id)},
        {"$inc": {"downloads": 1}}
    )

    file = fs.get(ObjectId(file_id))

    return send_file(
        io.BytesIO(file.read()),
        mimetype="application/pdf",
        download_name=file.filename,
        as_attachment=False
    )

# -------------------------------------------------
# PREVIEW PDF
# -------------------------------------------------
@app.route("/preview/<file_id>")
def preview_pdf(file_id):
    if "user_id" not in session:
        return redirect("/")

    material = materials.find_one({"file_id": ObjectId(file_id)})

    if not material:
        return "PDF not found"

    return render_template(
        "preview.html",
        file_id=file_id,
        title=material["title"],
        subject=material["subject"]
    )

# -------------------------------------------------
# ADMIN UPLOAD PAGE
# -------------------------------------------------
@app.route("/admin/upload")
def admin_upload():
    if session.get("role") != "admin":
        return redirect("/dashboard")

    return render_template("admin_upload.html")

# -------------------------------------------------
# ADMIN UPLOAD PDF
# -------------------------------------------------
@app.route("/admin/upload_pdf", methods=["POST"])
def upload_pdf():
    if session.get("role") != "admin":
        return redirect("/dashboard")

    if "pdf" not in request.files:
        flash("No file selected", "danger")
        return redirect("/admin/upload")

    pdf = request.files["pdf"]

    if pdf.filename == "" or not allowed_file(pdf.filename):
        flash("Only PDF files are allowed", "danger")
        return redirect("/admin/upload")

    filename = secure_filename(pdf.filename)

    category = request.form.get("category")
    title = request.form.get("title")
    subject = request.form.get("subject")

    if not category or not title or not subject:
        flash("All required fields must be filled", "danger")
        return redirect("/admin/upload")

    file_id = fs.put(pdf, filename=filename, contentType="application/pdf")

    if category == "study_material":
        materials.insert_one({
            "title": title,
            "subject": subject,
            "category": "study_material",
            "downloads": 0,
            "file_id": file_id
        })
        flash("Study material uploaded successfully", "success")

    elif category == "question_paper":
        year = request.form.get("year")
        paper_type = request.form.get("paper_type")

        if not year or not paper_type:
            flash("Year and Paper Type required for question papers", "danger")
            return redirect("/admin/upload")

        materials.insert_one({
            "title": title,
            "subject": subject,
            "category": "question_paper",
            "year": year,
            "paper_type": paper_type,
            "downloads": 0,
            "file_id": file_id
        })
        flash("Question paper uploaded successfully", "success")

    else:
        flash("Invalid upload category", "danger")

    return redirect("/admin/upload")

# -------------------------------------------------
# DELETE MATERIAL
# -------------------------------------------------
@app.route("/admin/delete/<material_id>")
def delete_material(material_id):
    if session.get("role") != "admin":
        return redirect("/dashboard")

    material = materials.find_one({"_id": ObjectId(material_id)})

    if material:
        fs.delete(material["file_id"])
        materials.delete_one({"_id": ObjectId(material_id)})
        flash("Deleted successfully", "success")

    return redirect(request.referrer or "/dashboard")

# -------------------------------------------------
# VIDEOS
# -------------------------------------------------
@app.route("/videos")
def videos():
    if "user_id" not in session:
        return redirect("/")

    return render_template("videos.html")

# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
