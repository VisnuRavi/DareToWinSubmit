from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from main.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    name = StringField('Name', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    repeat_password = PasswordField('Repeat Password', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
#        if username.data.find('+') != -1:
#            raise ValidationError('Please do not use "+" inside your username') #harder to manipulate url with +, if username has space, when use request.path becomes '+' instead of %20 which i think flask cant read. if remove spaces, if someone registers %20 as part of username can break system so need to remove both space and %20. other option to just remove + only
        user = User.query.filter_by(username = username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username')

    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email')

class LoginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UploadDareForm(FlaskForm):
    dare_desc = TextAreaField('Describe your dare!', validators = [DataRequired(), Length(min=1, max=20)])
    dare_vid = FileField('Dare Video', validators = [FileRequired(), FileAllowed(['mp4'], 'Please upload videos of .mp4 extensions only')])
    submit = SubmitField('Upload')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    about_me = TextAreaField('About me', validators = [Length(min=1, max=20)])
    submit = SubmitField('Submit')
    
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if self.original_username != username.data:
            user = User.query.filter_by(username = username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')
    

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    content = StringField('Add comment', validators = [DataRequired()])
    submit = SubmitField('Submit')


class SearchProfileForm(FlaskForm):
    username = StringField('Profile')
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user is None:
            raise ValidationError('Username not Found')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New password', validators = [DataRequired()])
    password2 = PasswordField('Repeat new password', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

    
class ReportForm(FlaskForm):
    report = TextAreaField('Report', validators = [DataRequired(), Length(min = 1)])
    submit = SubmitField('Submit')
