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
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


def send_confirm(user, token):
    """
    This function sends a confirmation email to the user.
    It generates the confirmation URL and calls the 'send_mail' function to send the email.
    """
    confirm_url = url_for('auth.confirm', token=token, _external=True)
    send_mail(user.email, 'Подтвердите свою учетную запись', 'auth/confirm', user=user, confirm_url=confirm_url)


def send_mail(to, subject, template, **kwargs):
    """
    This function sends an email using the Flask-Mail extension.
    It creates a new email message with the given subject, sender, and recipient.
    The email body is rendered from the specified template, and the message is sent asynchronously using a separate thread.
    """
    msg = Message(subject, sender="mirnatik2@gmail.com", recipients=[to])
    try:
        msg.html = render_template(template + ".html", **kwargs)
    except:
        msg.body = render_template(template + ".txt", **kwargs)
    from app_file import flask_app
    thread = Thread(target=send_async_email, args=[flask_app, msg])
    thread.start()
    return thread


def send_async_email(app, msg):
    """
    This function sends an email asynchronously using the Flask-Mail extension.
    It takes the Flask application and the email message as arguments, and sends the message within the application context.
    """
    with app.app_context():
        mail.send(msg)
