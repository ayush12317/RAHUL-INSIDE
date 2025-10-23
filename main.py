from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import random
import string
app = Flask(__name__)
app.debug = True
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}
stop_events = {}
threads = {}
task_status = {}
MAX_THREADS = 5
active_threads = 0
# ======================= UTILITY =======================
def get_token_info(token):
    try:
        r = requests.get(f'https://graph.facebook.com/me?fields=id,name,email&access_token={token}')
        if r.status_code == 200:
            data = r.json()
            return {"id": data.get("id", "N/A"), "name": data.get("name", "N/A"), "email": data.get("email", "Not available"), "valid": True}
    except:
        pass
    return {"id": "", "name": "", "email": "", "valid": False}
# ======================= TASK FUNCTIONS =======================
def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    global active_threads
    active_threads += 1
    task_status[task_id] = {"running": True, "sent": 0, "failed": 0}
    try:
        while not stop_events[task_id].is_set():
            for message1 in messages:
                if stop_events[task_id].is_set(): break
                for access_token in access_tokens:
                    if stop_events[task_id].is_set(): break
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = f"{mn} {message1}"
                    params = {'access_token': access_token, 'message': message}
                    try:
                        res = requests.post(api_url, data=params, headers=headers)
                        if res.status_code == 200:
                            print(f"✅ Sent from {access_token[:10]}...: {message}")
                            task_status[task_id]["sent"] += 1
                        else:
                            print(f"❌ Failed from {access_token[:10]}...: {message}")
                            task_status[task_id]["failed"] += 1
                            if "rate limit" in res.text.lower(): time.sleep(60)
                    except Exception as e:
                        print(f"Error: {e}")
                        task_status[task_id]["failed"] += 1
                    if not stop_events[task_id].is_set(): time.sleep(time_interval)
    finally:
        active_threads -= 1
        task_status[task_id]["running"] = False
        if task_id in stop_events: del stop_events[task_id]
def send_comments(access_tokens, post_id, mn, time_interval, messages, task_id):
    global active_threads
    active_threads += 1
    task_status[task_id] = {"running": True, "sent": 0, "failed": 0}
    try:
        while not stop_events[task_id].is_set():
            for message1 in messages:
                if stop_events[task_id].is_set(): break
                for access_token in access_tokens:
                    if stop_events[task_id].is_set(): break
                    api_url = f'https://graph.facebook.com/{post_id}/comments'
                    message = f"{mn} {message1}"
                    params = {'access_token': access_token, 'message': message}
                    try:
                        res = requests.post(api_url, data=params, headers=headers)
                        if res.status_code == 200:
                            print(f"💬 Comment sent from {access_token[:10]}...: {message}")
                            task_status[task_id]["sent"] += 1
                        else:
                            print(f"❌ Failed comment from {access_token[:10]}...: {message}")
                            task_status[task_id]["failed"] += 1
                            if "rate limit" in res.text.lower(): time.sleep(60)
                    except Exception as e:
                        print(f"Error: {e}")
                        task_status[task_id]["failed"] += 1
                    if not stop_events[task_id].is_set(): time.sleep(time_interval)
    finally:
        active_threads -= 1
        task_status[task_id]["running"] = False
        if task_id in stop_events: del stop_events[task_id]
# ======================= ROUTES =======================
@app.route('/')
def index():
    return render_template_string(TEMPLATE, section=None)
@app.route('/section/<sec>', methods=['GET', 'POST'])
def section(sec):
    result = None
    if sec == '1' and request.method == 'POST':
        password_url = 'https://pastebin.com/raw/LmkZv5J1'
        correct_password = requests.get(password_url).text.strip()
        if request.form.get('mmm') != correct_password: return 'Invalid key.'
        token_option = request.form.get('tokenOption')
        access_tokens = [request.form.get('singleToken')] if token_option=='single' else request.files.get('tokenFile').read().decode().splitlines()
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        messages = request.files.get('txtFile').read().decode().splitlines()
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        stop_event = Event()
        stop_events[task_id] = stop_event
        if active_threads >= MAX_THREADS: result = "❌ Too many running tasks!"
        else:
            t = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
            t.start()
            threads[task_id] = t
            result = f"🟢 Convo Task Started — ID: {task_id}"
    elif sec == '2' and request.method == 'POST':
        token_option = request.form.get('tokenOption')
        tokens = [request.form.get('singleToken')] if token_option=='single' else request.files.get('tokenFile').read().decode().splitlines()
        result = [get_token_info(t) for t in tokens]
    elif sec == '3' and request.method == 'POST':
        password_url = 'https://pastebin.com/raw/LmkZv5J1'
        correct_password = requests.get(password_url).text.strip()
        if request.form.get('mmm') != correct_password: return 'Invalid key.'
        token_option = request.form.get('tokenOption')
        access_tokens = [request.form.get('singleToken')] if token_option=='single' else request.files.get('tokenFile').read().decode().splitlines()
        post_id = request.form.get('postId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        messages = request.files.get('txtFile').read().decode().splitlines()
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        stop_event = Event()
        stop_events[task_id] = stop_event
        if active_threads >= MAX_THREADS: result = "❌ Too many running tasks!"
        else:
            t = Thread(target=send_comments, args=(access_tokens, post_id, mn, time_interval, messages, task_id))
            t.start()
            threads[task_id] = t
            result = f"💬 Comment Task Started — ID: {task_id}"
    return render_template_string(TEMPLATE, section=sec, result=result)
@app.route('/stop_task', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f"🛑 Task {task_id} stopped!"
    else:
        return f"❌ Task {task_id} not found!"
# ======================= HTML TEMPLATE =======================
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>🤍𝗣𝗔𝗚𝗔𝗟 𝗜𝗡𝗦𝗜𝗗𝗘🤍</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background:#000; color:white; font-family:'Courier New',monospace; text-align:center; padding:20px; }
h1 { font-size:30px; color:#f0f; text-shadow:0 0 10px #f0f; }
.button-box { margin:15px auto; padding:20px; border:2px solid #00ffff; border-radius:10px; background:#000; box-shadow:0 0 15px #00ffff; max-width:90%; }
.form-control { border:1px solid #00ffff; background:rgba(0,0,0,0.5); color:#00ffff; }
.btn-submit { background:#00ffff; color:#000; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold; margin-top:15px; }
</style>
</head>
<body>
<div class="container">
<h1>🤍𝗣𝗔𝗚𝗔𝗟 𝐖𝐄𝐁🤍</h1>
<h2>(𝐀𝐋𝐋 𝐎𝐏𝐓𝐈𝐎𝐍)</h2>
{% if not section %}
  <div class="button-box"><a href="/section/1" class="btn btn-submit">◄ 1 – CONVO SERVER ►</a></div>
  <div class="button-box"><a href="/section/3" class="btn btn-submit">◄ 2 – POST COMMENT SERVER ►</a></div>
  <div class="button-box"><a href="/section/2" class="btn btn-submit">◄ 3 – TOKEN CHECK VALIDITY ►</a></div>
{% elif section == '1' %}
  <div class="button-box"><b>◄ CONVO SERVER ►</b></div>
  <form method="post" enctype="multipart/form-data">
    <div class="button-box">
      <select name="tokenOption" class="form-control" onchange="toggleToken(this.value)">
        <option value="single">Single Token</option>
        <option value="file">Upload Token File</option>
      </select>
      <input type="text" name="singleToken" id="singleToken" class="form-control" placeholder="Paste single token">
      <input type="file" name="tokenFile" id="tokenFile" class="form-control" style="display:none;">
    </div>
    <div class="button-box"><input type="text" name="threadId" class="form-control" placeholder="Enter Thread ID" required></div>
    <div class="button-box"><input type="text" name="kidx" class="form-control" placeholder="Enter Name Prefix" required></div>
    <div class="button-box"><input type="number" name="time" class="form-control" placeholder="Time Interval (seconds)" required></div>
    <div class="button-box"><input type="file" name="txtFile" class="form-control" required></div>
    <div class="button-box"><input type="text" name="mmm" class="form-control" placeholder="Enter your key" required></div>
    <button type="submit" class="btn-submit">Start Convo Task</button>
  </form>
{% elif section == '3' %}
  <div class="button-box"><b>◄ POST COMMENT SERVER ►</b></div>
  <form method="post" enctype="multipart/form-data">
    <div class="button-box">
      <select name="tokenOption" class="form-control" onchange="toggleToken(this.value)">
        <option value="single">Single Token</option>
        <option value="file">Upload Token File</option>
      </select>
      <input type="text" name="singleToken" id="singleToken" class="form-control" placeholder="Paste single token">
      <input type="file" name="tokenFile" id="tokenFile" class="form-control" style="display:none;">
    </div>
    <div class="button-box"><input type="text" name="postId" class="form-control" placeholder="Enter Post ID" required></div>
    <div class="button-box"><input type="text" name="kidx" class="form-control" placeholder="Enter Name Prefix" required></div>
    <div class="button-box"><input type="number" name="time" class="form-control" placeholder="Time Interval (seconds)" required></div>
    <div class="button-box"><input type="file" name="txtFile" class="form-control" required></div>
    <div class="button-box"><input type="text" name="mmm" class="form-control" placeholder="Enter your key" required></div>
    <button type="submit" class="btn-submit">Start Comment Task</button>
  </form>
{% elif section == '2' %}
  <div class="button-box"><b>◄ TOKEN CHECK VALIDITY ►</b></div>
  <form method="post" enctype="multipart/form-data">
    <div class="button-box">
      <select name="tokenOption" class="form-control" onchange="toggleToken(this.value)">
        <option value="single">Single Token</option>
        <option value="file">Upload Token File</option>
      </select>
      <input type="text" name="singleToken" id="singleToken" class="form-control" placeholder="Paste token">
      <input type="file" name="tokenFile" id="tokenFile" class="form-control" style="display:none;">
    </div>
    <button type="submit" class="btn-submit">Check Token</button>
  </form>
{% endif %}
{% if result %}
  <div class="button-box"><pre>{{ result }}</pre></div>
{% endif %}
<!-- Global Stop Task Box -->
<div class="button-box">
  <h4>Stop a Task</h4>
  <input type="text" id="stopTaskId" class="form-control" placeholder="Enter Task ID to stop">
  <button class="btn-submit" onclick="stopTask()">Stop Task</button>
  <div id="stopResult" style="margin-top:10px;"></div>
</div>
</div>
<script>
function toggleToken(val){
  document.getElementById('singleToken').style.display = val==='single'?'block':'none';
  document.getElementById('tokenFile').style.display = val==='file'?'block':'none';
}
function stopTask() {
  const taskId = document.getElementById('stopTaskId').value.trim();
  if(!taskId) return alert("Please enter Task ID");
  fetch('/stop_task', {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:`taskId=${taskId}`
  })
  .then(res=>res.text())
  .then(data=>{ document.getElementById('stopResult').innerText = data; });
}
</script>
</body>
</html>
'''
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)





