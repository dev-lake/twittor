from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,\
                    TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError,\
                                Length

from twittor.models.user import User

class LoginForm(FlaskForm):
    # class Meta:
    #     csrf = False
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Password Repeat", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please input different username.')

    def validate_username(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please input different email.')

class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me', validators=[Length(0, 120)])
    submit = SubmitField('Save')

class TweetForm(FlaskForm):
    tweet = TextAreaField('About me', validators=[DataRequired(), Length(1, 120)])
    submit = SubmitField('Tweet')

class PasswdResetRequestForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('You don\'t have an account for this email.')

class PasswdResetForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Password Repeat", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Submit')
