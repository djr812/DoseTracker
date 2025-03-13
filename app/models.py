from app.extensions import db, bcrypt

# Users table for storing user information
class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # One-to-many relationship: One user can have many user_medicines
    user_medicines = db.relationship('UserMedicine', backref='user', lazy=True)

    def is_active(self):
        return True  

    def is_authenticated(self):
        return True  

    def is_anonymous(self):
        return False  

    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f"<User {self.email}>"

# Medicines table to store the medicine information
class Medicine(db.Model):
    
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # One-to-many relationship: One medicine can be associated with many user_medicines
    user_medicines = db.relationship('UserMedicine', backref='medicine', lazy=True)

    def __repr__(self):
        return f"<Medicine {self.name}>"

# User-Medicine table for storing user-specific data about medicines they are tracking
class UserMedicine(db.Model):
    
    __tablename__ = 'user_medicines'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    dosage = db.Column(db.String(255), nullable=False)
    frequency = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<UserMedicine User: {self.user_id}, Medicine: {self.medicine_id}>"