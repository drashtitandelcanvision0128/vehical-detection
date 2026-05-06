"""
Authentication HTML Templates
Contains login and register page templates
"""

# Login Template - Matching App Theme
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Login - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">analytics</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Enterprise Vehicle Intelligence</h1>
            <p class="text-secondary mt-2">Sign in to access vehicle detection</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message|safe }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="/login">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Email</label>
                    <input type="email" name="email" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your email">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Password</label>
                    <input type="password" name="password" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your password">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">login</span>
                    Sign In
                </button>
            </div>
        </form>

        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                Don't have an account? 
                <a href="/register" class="text-primary font-semibold hover:underline">Register here</a>
            </p>
            <p class="mt-2">
                <a href="/forgot-password" class="text-sm text-primary font-semibold hover:underline">Forgot Password?</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""

# Register Template - Matching App Theme
REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Register - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">analytics</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Enterprise Vehicle Intelligence</h1>
            <p class="text-secondary mt-2">Create your account</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message|safe }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="/register">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Username</label>
                    <input type="text" name="username" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Choose a username">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Email</label>
                    <input type="email" name="email" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your email">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Password</label>
                    <input type="password" name="password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Create a password (min 6 characters)">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Confirm Password</label>
                    <input type="password" name="confirm_password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Confirm your password">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">person_add</span>
                    Create Account
                </button>
            </div>
        </form>

        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                Already have an account? 
                <a href="/login" class="text-primary font-semibold hover:underline">Sign in here</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""

# Forgot Password Template - Matching App Theme
FORGOT_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Forgot Password - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">lock_reset</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Forgot Password</h1>
            <p class="text-secondary mt-2">Enter your email to receive a reset link</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message|safe }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="/forgot-password">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Email Address</label>
                    <input type="email" name="email" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your registered email">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">send</span>
                    Send Reset Link
                </button>
            </div>
        </form>

        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                Remember your password? 
                <a href="/login" class="text-primary font-semibold hover:underline">Sign in here</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""

# Reset Password Template - Matching App Theme
RESET_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Reset Password - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">key</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Reset Password</h1>
            <p class="text-secondary mt-2">Enter your new password</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message|safe }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="/reset-password/{{ token }}">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">New Password</label>
                    <input type="password" name="new_password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter new password (min 6 characters)">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Confirm New Password</label>
                    <input type="password" name="confirm_password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Confirm new password">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">check_circle</span>
                    Reset Password
                </button>
            </div>
        </form>

        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                <a href="/login" class="text-primary font-semibold hover:underline">Back to Login</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""
