from app.extensions import db
from flask_security import UserMixin, RoleMixin
import uuid

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'Role: {self.name}>'



# Association table
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # UPDATED
    def get_primary_role(self):
        if self.roles:
            return self.roles[0].name.replace('_', ' ').title()
        return "No Role Assigned"
    
    
    # Account status fields
    active = db.Column(db.Boolean(), default=True)
    confirmed_at = db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(), nullable=False, default=db.func.current_timestamp())
    
    # Unique identifier for Flask-Security
    # This is used to ensure that the user can be uniquely identified across sessions
    # and is particularly useful in distributed systems.
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    

    
    # County and department associations
    county_id = db.Column(db.Integer, db.ForeignKey('counties.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))

    # Tracking fields
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(50))
    current_login_ip = db.Column(db.String(50))
    login_count = db.Column(db.Integer, default=0)

    # Profile information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # Relationship
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email.split('@')[0] # Fallback if user dont provide first and last name or both

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        role_names = [role.name for role in self.roles]
        return f'User: {self.email}> Roles: {role_names}'
