from app import db, UserMixin
from app import bcrypt
from sqlalchemy.sql import func
from sqlalchemy import DateTime


class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    uuid = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255), nullable=True)
    firstname = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    job = db.Column(db.Integer, db.ForeignKey('Job.id'))
    role = db.Column(db.String(64), nullable=False)
    cookie = db.Column(db.String(255), unique=True, nullable=True)
    OTPSecret = db.Column(db.String(255), unique=True, nullable=True)
    codeEP = db.Column(db.String(255), unique=True, nullable=True)
    picture = db.Column(db.String(1024), unique=True, nullable=True)
    enable = db.Column(db.Integer, nullable=True, default=1)
    firstCon = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')


class Job(db.Model):
    __tablename__ = 'Job'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


class USBlog(db.Model):
    __tablename__ = 'USBlog'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    virus = db.Column(db.Integer, default=0)
    date = db.Column(DateTime(timezone=True), server_default=func.now())
    idUser = db.Column(db.Integer, db.ForeignKey('Users.id'))
    idSlave = db.Column(db.Integer, db.ForeignKey('Endpoint.id'))


class Endpoint(db.Model):
    __tablename__ = 'Endpoint'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    ip = db.Column(db.String(64), nullable=False, unique=True)
    token = db.Column(db.String(255), nullable=False, unique=True)
    hostname = db.Column(db.String(255), nullable=True)
    state = db.Column(db.Integer, nullable=False)

# class Alerts(db.Model):
#    __tablename__ = "Alerts"
#    id = db.Column(db.Integer,primary_key=True,unique=True)
#    timestamp = db.Column(db.String(255))
#    name = db.Column(db.String(255),nullable=False)
#    description = db.Column(db.String(255),nullable=False)
#    tag = db.Column(db.String(255),nullable=False)
#    has_read = db.Column(db.Integer,nullable=False,default=0)


class Setup(db.Model):
    __tablename__ = 'Setup'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    action = db.Column(db.String(255), nullable=False, unique=True)
    state = db.Column(db.Boolean, default=False)
