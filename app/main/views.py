import os
from flask import request, current_app
from app.models import DancingClasses, User, Review
from ..decorators import admin_required
from flask_login import login_required, current_user
from flask import redirect, url_for, render_template
from werkzeug.utils import secure_filename
from app.main.forms import ClassesForm, ReviewForm
from app.main import main
from app import db


@main.route("/user/<name>")
def hello_user(name):
    """This function takes a name parameter and returns an HTML response with a greeting message.

    Args:
        name (str): The name of the user to be used in the greeting.

    Returns:
        str: An HTML string with the greeting message.
    """
    return '<h2>Hello, {}</h2>'.format(name)


@main.route("/user_info")
def info():
    """This function retrieves the user's IP address and browser information
    and returns an HTML response displaying this information.

    Returns:
        str: An HTML string containing the user's IP address and browser information.
    """
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    return '<h2>Your IP address is {}/</h2><h2>Your browser is {}</h2>'.format(user_ip, user_agent)


@main.route("/")
def index():
    """This function renders the 'ind.html' template and returns the rendered HTML.

    Returns:
        str: The rendered HTML of the 'ind.html' template.
    """
    return render_template('ind.html')


@main.route('/secret')
@login_required
def secret():
    """This function is accessible only to authenticated users and returns the string 'Only for auth'.

    Returns:
        str: The string 'Only for auth'.
    """
    return "Only for auth"


@main.route('/admin')
@login_required
@admin_required
def for_admin():
    """This function is accessible only to users with the 'admin' role and returns the string 'For admin'.

    Returns:
        str: The string 'For admin'.
    """
    return "For admin"


@main.route("/testConfirm")
def testConfirm():
    """This function retrieves the first user from the database, generates a
    confirmation token for the user, and then confirms the user.
    """
    user = User.query.filter_by().first()
    tmp = user.generate_confirmation_token()
    user.confirm(tmp)


@main.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    review_count = Review.query.filter_by(user_id=user.id).count()
    return render_template('profile.html', user=user, review_count=review_count)


@main.route('/classes')
def classes():
    """This function retrieves all the dancing classes from the database and renders
    the 'classes.html' template with the classes data.

    Returns:
        str: The rendered HTML of the 'classes.html' template with the dancing classes data.
    """
    dancings = DancingClasses.query.all()
    return render_template('classes.html', dancings=dancings)


@main.route('/create_classes', methods=['GET', 'POST'])
@admin_required
def create_classes():
    """This function handles the creation of new dancing classes. It renders the
    'create_classes.html' template with a form, and when the form is submitted, it creates
    a new DancingClasses instance, saves the video file (if provided), and adds the new class to the database.

    Returns:
        str: The rendered HTML of the 'create_classes.html' template if the form is not submitted,
             or a redirect to the index page if the form is successfully submitted.
    """
    form = ClassesForm()
    if form.validate_on_submit():
        dancing = DancingClasses(
            title=form.title.data,
            description=form.description.data,
            datetime=form.datetime.data,
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
    dancing = DancingClasses.query.get_or_404(dancing_id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(comments=form.comments.data, rating=form.rating.data, user_id=current_user.id, dancing_id=dancing.id)
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('main.classes_detail', dancing_id=dancing_id))
    reviews = Review.query.filter_by(dancing_id=dancing_id).all()
    return render_template('classes_detail.html', form=form, dancing=dancing, reviews=reviews)