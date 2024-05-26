from flask_wtf import FlaskForm
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, EmailField, SubmitField, URLField
from wtforms.validators import DataRequired, Email, Length


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email= EmailField('Email', validators=[DataRequired(),Email()])
    password=StringField('Password', validators=[DataRequired(),Length(min=8)])
    ktp= StringField('Nomor Induk KTP',validators=[DataRequired(),Length(min=16)])
    submit = SubmitField("Register")

class AddClass(FlaskForm):
    name= StringField('Name', validators=[DataRequired()])
    submit= SubmitField("Add")

class SubmitAssignment(FlaskForm):
    class_id=StringField('Class ID', validators=[DataRequired()])
    # student_name=StringField('Student Name',validators=[DataRequired()])
    url=URLField('Assignment URL',validators=[DataRequired()])
    submit = SubmitField("Submit Assignment")

class LoginForm(FlaskForm):
    email= EmailField('Email', validators=[DataRequired(),Email()])
    password=StringField('Password', validators=[DataRequired(),Length(min=8)])
    submit = SubmitField("Login")

class EditAssignment(FlaskForm):
    url = URLField('Assignment URL', validators=[DataRequired()])
    submit = SubmitField("Update Assignment")