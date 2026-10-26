from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)

DATABASE = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            goals TEXT,
            preferences TEXT,
            tasks TEXT,
            summary TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# Create the database table when the app starts
init_db()


def extract_memory(conversation):
    text = conversation.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)

    goals = []
    preferences = []
    tasks = []

    for sentence in sentences:
        lower_sentence = sentence.lower()

        if any(keyword in lower_sentence for keyword in [
            "want to", "my goal", "aim to", "i plan to",
            "i need to", "i hope to"
        ]):
            goals.append(sentence.strip())

        if any(keyword in lower_sentence for keyword in [
            "i prefer", "i like", "i don't like",
            "i dislike", "prefer"
        ]):
            preferences.append(sentence.strip())

        if any(keyword in lower_sentence for keyword in [
            "build", "create", "complete", "learn",
            "develop", "practice", "work on"
        ]):
            tasks.append(sentence.strip())

    if not goals:
        goals.append("No specific goals detected.")

    if not preferences:
        preferences.append("No specific preferences detected.")

    if not tasks:
        tasks.append("No specific tasks detected.")

    summary = (
        f"This memory contains {len(sentences)} conversation statements. "
        f"It includes {len(goals)} goal-related statements, "
        f"{len(preferences)} preference-related statements, and "
        f"{len(tasks)} task-related statements."
    )

    return {
        "goals": goals,
        "preferences": preferences,
        "tasks": tasks,
        "summary": summary
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/capture")
def capture():
    return render_template("capture.html")


@app.route("/generate", methods=["POST"])
def generate():
    title = request.form.get("title", "Untitled Memory")
    conversation = request.form.get("conversation", "")

    extracted = extract_memory(conversation)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO memories
        (title, goals, preferences, tasks, summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        "\n".join(extracted["goals"]),
        "\n".join(extracted["preferences"]),
        "\n".join(extracted["tasks"]),
        extracted["summary"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()

    return redirect(f"/memory/{memory_id}")


@app.route("/memory/<int:memory_id>")
def view_memory(memory_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    memory = conn.execute(
        "SELECT * FROM memories WHERE id = ?",
        (memory_id,)
    ).fetchone()

    conn.close()

    if memory is None:
        return "Memory not found", 404

    return render_template("memory.html", memory=memory)


@app.route("/context/<int:memory_id>")
def context_pack(memory_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    memory = conn.execute(
        "SELECT * FROM memories WHERE id = ?",
        (memory_id,)
    ).fetchone()

    conn.close()

    if memory is None:
        return "Memory not found", 404

    return render_template("context.html", memory=memory)


@app.route("/delete/<int:memory_id>", methods=["POST"])
def delete_memory(memory_id):
    conn = sqlite3.connect(DATABASE)

    conn.execute(
        "DELETE FROM memories WHERE id = ?",
        (memory_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/memories")


@app.route("/memories")
def memories():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    all_memories = conn.execute(
        "SELECT * FROM memories ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "memories.html",
        memories=all_memories
    )


if __name__ == "__main__":
    app.run(debug=True)