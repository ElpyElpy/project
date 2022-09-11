from flask import redirect, render_template, request, session
from functools import wraps


# This function checks registration form parameters
def complete_registration(user_name, password, confirmation):
    # Ensure username was submitted
    if not user_name:
        print(f"username: {user_name}")
        alert = "missing name"
        return render_template("register.html", alert=alert)

    # Ensure password was submitted
    if not password:
        alert = "missing password"
        return render_template("register.html", alert=alert)

    # Ensure passwords are the same
    if password != confirmation:
        alert = "pwds different"
        return render_template("register.html", alert=alert)

    # save user_id
    session["user_id"] = 1

    return render_template("main_page.html")


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
