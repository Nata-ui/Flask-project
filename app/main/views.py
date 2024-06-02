import os
from flask import request, current_app
from app.models import Permission, DancingClasses, User
from ..decorators import admin_required, permission_required
from flask_login import login_required, current_user
from flask import redirect, url_for, render_template
from werkzeug.utils import secure_filename
from app.main.forms import ClassesForm
from app.main import main
from app import db


@main.route("/user/<name>")
def hello_user(name):
    """This function takes a `name` parameter and returns an HTML response with a greeting message."""
    return '<h2>Hello, {}</h2>'.format(name)


@main.route("/user_info")
def info():
    """This function retrieves the user's IP address and browser information
    and returns an HTML response displaying this information."""
    user_ip = request.remote_addr
    user_agent = request.headers.get ('User-Agent')
    return '<h2>Your IP address is {}/</h2><h2>Your browser is {}</h2>'. format(user_ip, user_agent)


@main.route("/")
def index():
    """This function renders the 'ind.html' template and returns the rendered HTML."""
    return render_template('ind.html')


@main.route('/secret')
@login_required
def secret():
    """This function is accessible only to authenticated users and returns the string 'Only for auth'."""
    return "Only for auth"


@main.route('/admin')
@login_required
@admin_required
def for_admin():
    """This function is accessible only to users with the 'admin' role and returns the string 'For admin'."""
    return "For admin"


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderator():
    """This function is accessible only to users with the 'moderate' permission
    and returns the string 'For moderator'."""
    return "For moderator"


@main.route("/testConfirm")
def testConfirm():
    """This function retrieves the first user from the database, generates a
    confirmation token for the user, and then confirms the user."""
    user = User.query.filter_by().first()
    tmp = user.generate_confirmation_token()
    user.confirm(tmp)


@main.route('/profile')
@login_required
def profile():
    """This function renders the 'profile.html' template and displays the current user's information."""
    return render_template('profile.html')


@main.route('/classes')
def classes():
    """This function retrieves all the dancing classes from the database and renders
    the 'classes.html' template with the classes data."""
    dancings = DancingClasses.query.all()
    return render_template('classes.html', dancings=dancings)


@main.route('/create_classes', methods=['GET', 'POST'])
@admin_required
def create_classes():
    """This function handles the creation of new dancing classes. It renders the
    'create_classes.html' template with a form, and when the form is submitted, it creates
    a new `DancingClasses` instance, saves the video file (if provided), and adds the new class to the database."""
    form = ClassesForm()
    if form.validate_on_submit():
        dancing = DancingClasses(
            title=form.title.data,
            description=form.description.data,
            time=form.time.data,
            category=form.category.data,
            trainer=current_user
        )
        if form.video.data:
            filename = secure_filename(form.video.data.filename)
            video_path = os.path.join(current_app.root_path, 'static', 'videos', filename)
            form.video.data.save(video_path)
            dancing.video_path = f'/static/videos/{filename}'
        db.session.add(dancing)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('create_classes.html', form=form)


@main.route('/dancing/<int:dancing_id>', methods=['GET', 'POST'])
@login_required
def classes_detail(dancing_id):
    """This function retrieves the dancing class with the given `dancing_id`
    and renders the 'classes_detail.html' template with the class data."""
    dancing = DancingClasses.query.get_or_404(dancing_id)
    return render_template('classes_detail.html', dancing=dancing)

