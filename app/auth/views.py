from flask import render_template, redirect, request, flash, url_for
from flask_mail import Message
from . import auth
from .forms import LoginForm, RegistrationForm
from .. import db, mail
from ..models import User
from flask_login import login_user, login_required, logout_user, current_user
from threading import Thread


@auth.before_app_request
def before_request():
    """
    This function is executed before any request is processed in the 'auth' blueprint.
    If the current user is authenticated, it updates the last seen time of the user.
    If the user is not confirmed and the request is not for the 'auth' blueprint, the 'static' endpoint, or the
    'auth.confirm' endpoint, the user is redirected to the 'auth.unconfirmed' endpoint.
    """
    if current_user.is_authenticated:
        current_user.ping()
        if (
                not current_user.confirmed
                and request.blueprint != 'auth'
                and request.endpoint != 'static'
                and request.endpoint != 'auth.confirm'
        ):
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function handles the user login process.
    It renders the login template and processes the login form submission.
    If the form is valid and the user credentials are correct, the user is logged in and redirected to the next page.
    If the credentials are invalid, a flash message is displayed.

    Returns:
        str: The rendered HTML of the 'auth/login.html' template if the form is not submitted,
             or a redirect to the next page if the form is successfully submitted.
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.password_verify(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get("next")
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid username or password')
    return render_template("auth/login.html", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    This function handles the user registration process.
    It renders the registration template and processes the registration form submission.
    If the form is valid, a new user is created, the password is hashed, and a confirmation token is generated and sent to the user's email.
    The user is then redirected to the login page.

    Returns:
        str: The rendered HTML of the 'auth/registration.html' template if the form is not submitted,
             or a redirect to the login page if the form is successfully submitted.
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data)
        db.session.add(user)
        user.set_password(form.password.data)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_confirm(user, token)
        flash("Register complete")
        return redirect(url_for('auth.login'))
    return render_template("auth/registration.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """
    This function handles the user logout process.
    It logs out the current user and redirects them to the main page.

    Returns:
        str: A redirect to the main page.
    """
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    """
    This function handles the user email confirmation process.
    If the current user is already confirmed, they are redirected to the main page.

    If the confirmation token is valid, the user's account is confirmed and they are redirected to the login page.
    If the token is invalid, a flash message is displayed and the user is redirected to the main page.

    Args:
        token (str): The confirmation token to be used for confirming the user's account.

    Returns:
        str: A redirect to the main page if the token is invalid, or a redirect to the login page if the token is valid.
    """
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash("Подтверждено")
        return redirect(url_for('auth.login'))
    else:
        flash("Ссылка не работает")

    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    """
    This function renders the 'unconfirmed' template if the current user is not confirmed.
    If the user is anonymous or confirmed, they are redirected to the main page.

    Returns:
        str: The rendered HTML of the 'auth/unconfirmed.html' template if the current user is not confirmed,
             or a redirect to the main page if the user is anonymous or confirmed.
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')
