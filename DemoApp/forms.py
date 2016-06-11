from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, IntegerField, FieldList, FormField, validators

class LoginForm(Form):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class RegistrationForm(Form):
    fullname = StringField('Full Name', [validators.Length(min=4, max=25)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('password2', message='Passwords must match')
    ])
    password2 = PasswordField('Confirm Password')
    accept_tos = BooleanField('I accept the Terms of Service', [validators.DataRequired()])


class IShipForm(Form):
    ship_name = StringField(40)
    quantity = IntegerField()

class BuildShipsForm(Form):
    ship_list = FieldList(FormField(IShipForm), [validators.DataRequired()])

class MoveFleetForm(Form):
    destination = IntegerField('destination', [validators.DataRequired()])
