# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Это разрешит запросы с любого сайта (включая твой HTML)
app = Flask(__name__)
CORS(app)

DB_USERS = "users.db"
DB_TASKS = "tasks.db"

def init_dbs():
    # База пользователей с поддержкой раздельной статистики
    with sqlite3.connect(DB_USERS) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            rus_total INTEGER DEFAULT 0,
                            rus_correct INTEGER DEFAULT 0,
                            rus_wrong INTEGER DEFAULT 0,
                            math_total INTEGER DEFAULT 0,
                            math_correct INTEGER DEFAULT 0,
                            math_wrong INTEGER DEFAULT 0)''')
        conn.commit()

    # База заданий
    with sqlite3.connect(DB_TASKS) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject TEXT NOT NULL,
                            theme TEXT NOT NULL,
                            text TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            pom_phrase TEXT)''')
        conn.commit()

init_dbs()

@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({"error": "Заполните все поля!"}), 400
    try:
        with sqlite3.connect(DB_USERS) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        return jsonify({"success": "Регистрация успешна!"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Этот логин уже занят!"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    with sqlite3.connect(DB_USERS) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT password, rus_total, rus_correct, rus_wrong, math_total, math_correct, math_wrong 
                          FROM users WHERE username = ?""", (username,))
        row = cursor.fetchone()
    
    if row and row[0] == password:
        return jsonify({
            "success": "Вход выполнен!",
            "stats": {
                "rus": {"total": row[1], "correct": row[2], "wrong": row[3]},
                "math": {"total": row[4], "correct": row[5], "wrong": row[6]}
            }
        }), 200
    return jsonify({"error": "Неверный логин или пароль!"}), 401

@app.route('/get_stats/<username>', methods=['GET'])
def get_stats(username):
    with sqlite3.connect(DB_USERS) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT rus_total, rus_correct, rus_wrong, math_total, math_correct, math_wrong 
                          FROM users WHERE username = ?""", (username,))
        row = cursor.fetchone()
    if row:
        return jsonify({
            "stats": {
                "rus": {"total": row[0], "correct": row[1], "wrong": row[2]},
                "math": {"total": row[3], "correct": row[4], "wrong": row[5]}
            }
        }), 200
    return jsonify({"error": "Пользователь не найден"}), 404

@app.route('/update_stats', methods=['POST'])
def update_stats():
    data = request.json or {}
    username = data.get('username', '').strip()
    subject = data.get('subject', '').strip()
    is_correct = data.get('is_correct', False)

    if subject not in ['rus', 'math']:return jsonify({"error": "Неверный предмет"}), 400

    field_total = f"{subject}_total"
    field_res = f"{subject}_correct" if is_correct else f"{subject}_wrong"

    with sqlite3.connect(DB_USERS) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {field_total} = {field_total} + 1, {field_res} = {field_res} + 1 WHERE username = ?", (username,))
        conn.commit()
    return jsonify({"success": "Статистика обновлена"}), 200

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    data = request.json or {}
    username = data.get('username', '').strip()
    with sqlite3.connect(DB_USERS) as conn:
        cursor = conn.cursor()
        cursor.execute("""UPDATE users SET 
                          rus_total=0, rus_correct=0, rus_wrong=0, 
                          math_total=0, math_correct=0, math_wrong=0 
                          WHERE username = ?""", (username,))
        conn.commit()
    return jsonify({"success": "Статистика сброшена"}), 200

@app.route('/get_task/<subject>', methods=['GET'])
def get_task(subject):
    with sqlite3.connect(DB_TASKS) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT theme, text, answer, pom_phrase FROM tasks WHERE subject = ?", (subject,))
        rows = cursor.fetchall()
    if not rows:
        return jsonify({"error": "Задания не найдены"}), 404
    task = random.choice(rows)
    return jsonify({"theme": task[0], "text": task[1], "answer": task[2], "pom_phrase": task[3]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)