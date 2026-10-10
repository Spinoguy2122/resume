from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "resumes.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            job_title TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            summary TEXT,
            education TEXT,
            university TEXT,
            experience TEXT,
            experience_details TEXT,
            skills TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return jsonify({
        "message": "Resume Builder API is running",
        "endpoints": [
            "GET /resumes",
            "GET /resumes/<id>",
            "POST /resumes",
            "PUT /resumes/<id>",
            "DELETE /resumes/<id>"
        ]
    })


@app.route("/resumes", methods=["POST"])
def create_resume():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    name = data.get("name", "").strip() if isinstance(data.get("name", ""), str) else ""

    if not name:
        return jsonify({"error": "Name is required"}), 400

    fields = [
        "name", "job_title", "email", "phone", "location",
        "summary", "education", "university", "experience",
        "experience_details", "skills"
    ]

    values = [name]

    for field in fields[1:]:
        value = data.get(field, "")
        if not isinstance(value, str):
            return jsonify({"error": f"{field} must be a string"}), 400
        values.append(value.strip())

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO resumes (
            name, job_title, email, phone, location, summary,
            education, university, experience, experience_details, skills
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, values)

    conn.commit()
    resume_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Resume created successfully",
        "id": resume_id
    }), 201


@app.route("/resumes", methods=["GET"])
def get_resumes():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM resumes ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/resumes/<int:resume_id>", methods=["GET"])
def get_resume(resume_id):
    conn = get_db_connection()

    row = conn.execute(
        "SELECT * FROM resumes WHERE id = ?",
        (resume_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return jsonify({"error": "Resume not found"}), 404

    return jsonify(dict(row))


@app.route("/resumes/<int:resume_id>", methods=["PUT"])
def update_resume(resume_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    fields = [
        "name", "job_title", "email", "phone", "location",
        "summary", "education", "university", "experience",
        "experience_details", "skills"
    ]

    if not data or any(field not in fields for field in data):
        return jsonify({"error": "Provide valid resume fields"}), 400

    if any(not isinstance(data[field], str) for field in data):
        return jsonify({"error": "All resume fields must be strings"}), 400

    if "name" in data and not data["name"].strip():
        return jsonify({"error": "Name cannot be empty"}), 400

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM resumes WHERE id = ?",
        (resume_id,)
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Resume not found"}), 404

    assignments = ", ".join(f"{field} = ?" for field in data)
    values = [data[field].strip() for field in data]
    values.append(resume_id)

    conn.execute(
        f"UPDATE resumes SET {assignments} WHERE id = ?",
        values
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Resume updated successfully"})


@app.route("/resumes/<int:resume_id>", methods=["DELETE"])
def delete_resume(resume_id):
    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM resumes WHERE id = ?",
        (resume_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if not deleted:
        return jsonify({"error": "Resume not found"}), 404

    return jsonify({"message": "Resume deleted successfully"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)