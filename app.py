from flask import Flask, request, render_template_string
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 🔍 Parse user response.html
def parse_response(html):
    soup = BeautifulSoup(html, "html.parser")
    user_answers = {}
    for block in soup.find_all("div", class_="question-pnl"):
        try:
            qid = block.find('td', string='Question ID :').find_next_sibling('td').text.strip()
            chosen = block.find('td', string='Chosen Option :').find_next_sibling('td').text.strip()
            user_answers[qid] = chosen
        except:
            continue
    return user_answers

# 🔍 Parse key.html
def parse_key(html):
    soup = BeautifulSoup(html, "html.parser")
    key_answers = {}
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 9:
            qid = cols[2].get_text(strip=True)
            correct_option_id = cols[3].get_text(strip=True)
            options = [cols[i].get_text(strip=True) for i in range(5, 9)]
            if correct_option_id in options:
                correct = options.index(correct_option_id) + 1
                key_answers[qid] = str(correct)
    return key_answers

# 🏠 Home with form + JS
@app.route('/')
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CUET Score Calculator</title>
  <style>
    body {
      background-color: #0D1117;
      color: #C9D1D9;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      padding: 40px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    h1 { color: #58A6FF; }
    form {
      max-width: 500px;
      width: 100%;
      background-color: #161B22;
      padding: 25px;
      border-radius: 10px;
      border: 1px solid #30363D;
      margin-bottom: 40px;
    }
    label {
      display: block;
      margin-top: 15px;
      margin-bottom: 5px;
    }
    input[type="file"] {
      width: 100%;
      padding: 10px;
      border: 1px solid #30363D;
      border-radius: 5px;
      background-color: #0D1117;
      color: #C9D1D9;
    }
    input[type="submit"] {
      background-color: #238636;
      color: white;
      border: none;
      padding: 12px 20px;
      border-radius: 5px;
      margin-top: 20px;
      width: 100%;
      cursor: pointer;
    }
    input[type="submit"]:hover {
      background-color: #2EA043;
    }
    #result {
      width: 90%;
      max-width: 1000px;
      background-color: #161B22;
      border: 1px solid #30363D;
      padding: 20px;
      border-radius: 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      color: #C9D1D9;
    }
    th, td {
      border: 1px solid #30363D;
      padding: 10px;
      text-align: center;
    }
    th { background-color: #21262D; }
  </style>
</head>
<body>
  <h1>CUET Score Calculator</h1>
  <form id="uploadForm" enctype="multipart/form-data">
    <label>Answer Key (HTML):</label>
    <input type="file" name="key" required>
    <label>Response Sheet (HTML):</label>
    <input type="file" name="response" required>
    <input type="submit" value="Calculate Score">
  </form>
  <div id="result"></div>
  <script>
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const res = await fetch('/upload', { method: 'POST', body: formData });
      const html = await res.text();
      document.getElementById('result').innerHTML = html;
    });
  </script>
</body>
</html>
    """)

# 📊 Upload logic
@app.route('/upload', methods=['POST'])
def upload():
    key_html = request.files['key'].read().decode('utf-8')
    response_html = request.files['response'].read().decode('utf-8')

    user_answers = parse_response(response_html)
    correct_answers = parse_key(key_html)

    score = 0
    correct_count = 0
    wrong_count = 0
    not_attempted_count = 0

    html = "<table><tr><th>Q.ID</th><th>Your Answer</th><th>Correct</th><th>Status</th></tr>"

    for qid, correct in correct_answers.items():
        user = user_answers.get(qid, "--").strip()

        if user in ["Not Attempted", "--", "-", "", None]:
            status = "—"
            not_attempted_count += 1
        elif user == correct:
            status = "✅"
            score += 5
            correct_count += 1
        else:
            status = "❌"
            score -= 1
            wrong_count += 1

        html += f"<tr><td>{qid}</td><td>{user}</td><td>{correct}</td><td>{status}</td></tr>"

    html += "</table><br>"
    html += f"<h2>Total Score: {score}</h2>"
    html += f"<p style='color:#2ea043;'>✅ Correct: {correct_count} (Marks: +{correct_count * 5})</p>"
    html += f"<p style='color:#e5534b;'>❌ Wrong: {wrong_count} (Marks: -{wrong_count})</p>"
    html += f"<p style='color:#999;'>➖ Not Attempted: {not_attempted_count}</p>"

    return html

if __name__ == '__main__':
    app.run(debug=True)
