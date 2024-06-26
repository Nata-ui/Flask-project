from wtforms import PasswordField
from wtforms.validators import InputRequired, NumberRange

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    username = StringField('Логин', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[InputRequired()])
    gender = SelectField('Пол', choices=[('M', 'Мужской'), ('F', 'Женский')])


class ClassesForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    datetime = DateTimeField('Date and Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    category = SelectField('Group', choices=['1', '2', '3'],
                           validators=[DataRequired()])
    video = FileField('Video', validators=[FileAllowed(['mp4', 'avi', 'mov'], 'Videos only!')])
    submit = SubmitField('Create class')


class ReviewForm(FlaskForm):
    comments = TextAreaField('Review', validators=[DataRequired()])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')