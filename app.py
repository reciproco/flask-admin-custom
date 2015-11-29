from flask import Flask,url_for, redirect, render_template, request
from wtforms import form, fields, validators
import flask_login as login
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import flask_admin as admin
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from werkzeug.security import generate_password_hash, check_password_hash


COMERCIAL = 1
# Create application
app = Flask(__name__)


# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db_2.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        #if not check_password_hash(user.password, self.password.data):
        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()

# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)

class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    desc = db.Column(db.String(50))
    model = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    hidden = db.Column(db.String(50))

    def __unicode__(self):
        return self.desc



class CarAdmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ['model','brand', 'desc']
    column_searchable_list = ['model', 'brand','desc']
    can_delete = False
    can_create = False
    can_export = True



    def get_query(self):
        return self.session.query(self.model).filter(self.model.hidden==login.current_user.login)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.hidden == login.current_user.login)
    def is_accessible(self):
        return login.current_user.is_authenticated

# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

init_login()

# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy2',index_view=MyAdminIndexView(), base_template='my_master.html', template_mode='bootstrap3')
admin.add_view(CarAdmin(Car, db.session))

def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import random
    import datetime

    db.drop_all()
    db.create_all()

    # Create sample Users
    desc = [
        'A', 'B', 'C', 'E', 'I', 'C', 'S', 'M',
        'J', 'T', 'E', 'A', 'A', 'I', 'A', 'O', 'J',
        'A', 'W', 'J', 'G', 'L', 'B', 'S', 'L'
    ]
    model = [
        'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
        'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
        'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
    ]
    brand = [
        'seat', 'citroen', 'renault', 'dig', 'juan', 'cpu', 'pol', 'Tas',
        'nissan', 'hyundai', 'mercedes', 'Jdodge', 'manolo', 'it', 'Pips', 'Wi',
        'wolswagen', 'skoda', 'bmw', 'Rose', 'pepe', 'ram', 'Roez', 'Cx', 'Al'
    ]
    hidden = [
        '1', '1', '1', '1', '1', '1', '1', '1',
        '2', '2', '2', '2', '2', '2', '3', '3',
        '3', '3', '3', '3', '3', '3', '3', '3', '3'
    ]

    car_list = []
    for i in range(len(desc)):
        car = Car()
        car.desc = desc[i]
        car.brand = brand[i].lower()
        car.hidden = hidden[i]
        car.model = model[i]
        car_list.append(car)
        db.session.add(car)

    user = User()
    user.login = '2'
    user.password = '1234'
    db.session.add(user)

    db.session.commit()

if __name__ == '__main__':

    # Create DB
    build_sample_db()

    # Start app
    app.run(debug=True)
