from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from mcrcon import MCRcon
import secrets
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# RCON Configuration
RCON_HOST = os.getenv('RCON_HOST', 'localhost')
RCON_PASSWORD = os.getenv('RCON_PASSWORD')
RCON_PORT = int(os.getenv('RCON_PORT', 25575))

# Website password
SITE_PASSWORD = "11223344"

# Skills configuration (1 coin = 2 XP)
SKILLS = {
    "farming": 2,
    "foraging": 2,
    "mining": 2,
    "fishing": 2,
    "excavation": 2,
    "archery": 2,
    "defense": 2,
    "fighting": 2,
    "endurance": 2,
    "agility": 2,
    "alchemy": 2
}

# Store tokens in memory (replace with database in production)
user_tokens = {}

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def send_rcon_command(command):
    """Send command to Minecraft server via RCON"""
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rcon:
            response = rcon.command(command)
            return response
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/api/healthcheck')
def healthcheck():
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == SITE_PASSWORD:
            session['authenticated'] = True
            return redirect('/')
        return "Invalid password!", 401

    return '''
    <html>
        <head>
            <title>Login - Minecraft XP Shop</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <div class="max-w-md mx-auto bg-white rounded-lg shadow p-6">
                    <h2 class="text-2xl font-bold mb-6">Enter Password</h2>
                    <form method="POST" class="space-y-4">
                        <div>
                            <label class="block text-gray-700">Password</label>
                            <input type="password" name="password" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
                        </div>
                        <button type="submit" class="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
                            Login
                        </button>
                    </form>
                </div>
            </div>
        </body>
    </html>
    '''

@app.route('/')
@require_auth
def index():
    return '''
    <html>
        <head>
            <title>Minecraft XP Shop</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-3xl font-bold mb-8 text-center">Minecraft XP Shop</h1>
                <div class="max-w-md mx-auto bg-white rounded-lg shadow p-6">
                    <div class="space-y-4">
                        <a href="/register" class="block w-full bg-blue-500 text-white text-center py-2 rounded hover:bg-blue-600">Register</a>
                        <a href="/shop" class="block w-full bg-green-500 text-white text-center py-2 rounded hover:bg-green-600">Shop</a>
                    </div>
                </div>
            </div>
        </body>
    </html>
    '''

@app.route('/register', methods=['GET', 'POST'])
@require_auth
def register():
    if request.method == 'POST':
        username = request.form.get('username')

        # Check if player exists in Minecraft
        response = send_rcon_command(f"bal {username}")
        if "not found" in response.lower():
            return "Player not found in Minecraft server!", 400

        # Generate access token
        token = secrets.token_urlsafe(16)
        user_tokens[username] = token

        return redirect(url_for('shop', username=username, token=token))

    return '''
    <html>
        <head>
            <title>Register - Minecraft XP Shop</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <div class="max-w-md mx-auto bg-white rounded-lg shadow p-6">
                    <h2 class="text-2xl font-bold mb-6">Register</h2>
                    <form method="POST" class="space-y-4">
                        <div>
                            <label class="block text-gray-700">Minecraft Username</label>
                            <input type="text" name="username" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
                        </div>
                        <button type="submit" class="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
                            Register
                        </button>
                    </form>
                </div>
            </div>
        </body>
    </html>
    '''

@app.route('/shop')
@require_auth
def shop():
    username = request.args.get('username')
    token = request.args.get('token')

    if not username or not token or user_tokens.get(username) != token:
        return redirect(url_for('index'))

    # Get player balance
    response = send_rcon_command(f"bal {username}")
    try:
        balance = float(response.split(":")[1].strip())
    except:
        balance = 0

    skills_html = ""
    for skill, rate in SKILLS.items():
        skills_html += f'<option value="{skill}">{skill.title()} ($1 = {rate} XP)</option>'

    return f'''
    <html>
        <head>
            <title>Shop - Minecraft XP Shop</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>
                function submitForm(event) {{
                    event.preventDefault();
                    const form = event.target;
                    const formData = new FormData(form);

                    fetch('/buy_xp', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            alert(data.message);
                            location.reload();
                        }} else {{
                            alert(data.error || 'An error occurred');
                        }}
                    }})
                    .catch(error => {{
                        alert('An error occurred');
                    }});
                }}
            </script>
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <div class="max-w-md mx-auto bg-white rounded-lg shadow p-6">
                    <h2 class="text-2xl font-bold mb-4">Welcome, {username}!</h2>
                    <p class="text-xl mb-6">Balance: ${balance:.2f}</p>

                    <form onsubmit="submitForm(event)" class="space-y-4">
                        <input type="hidden" name="username" value="{username}">
                        <input type="hidden" name="token" value="{token}">

                        <div>
                            <label class="block text-gray-700">Select Skill</label>
                            <select name="skill" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
                                {skills_html}
                            </select>
                        </div>

                        <div>
                            <label class="block text-gray-700">Amount ($)</label>
                            <input type="number" name="amount" min="1" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
                        </div>

                        <button type="submit" class="w-full bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600">
                            Buy XP
                        </button>
                    </form>
                </div>
            </div>
        </body>
    </html>
    '''

@app.route('/buy_xp', methods=['POST'])
@require_auth
def buy_xp():
    username = request.form.get('username')
    token = request.form.get('token')
    skill = request.form.get('skill')

    try:
        amount = float(request.form.get('amount', 0))
    except:
        return jsonify({"error": "Invalid amount"}), 400

    # Validate token
    if not username or not token or user_tokens.get(username) != token:
        return jsonify({"error": "Invalid session"}), 401

    # Validate skill
    if skill not in SKILLS:
        return jsonify({"error": "Invalid skill"}), 400

    # Check balance
    balance_response = send_rcon_command(f"bal {username}")
    try:
        balance = float(balance_response.split(":")[1].strip())
    except:
        return jsonify({"error": "Could not fetch balance"}), 400

    if balance < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    # Calculate XP
    xp_amount = int(amount * SKILLS[skill])

    # Process transaction
    try:
        # Deduct money
        eco_response = send_rcon_command(f"eco take {username} {amount}")
        if "taken" not in eco_response.lower():
            return jsonify({"error": "Failed to process payment"}), 400

        # Add XP
        xp_response = send_rcon_command(f"skills xp add {username} {skill} {xp_amount}")

        return jsonify({
            "success": True,
            "message": f"Successfully purchased {xp_amount:,} XP for {skill}",
            "new_balance": balance - amount
        })

    except Exception as e:
        # Attempt to refund
        send_rcon_command(f"eco give {username} {amount}")
        return jsonify({"error": str(e)}), 500
