from app.extensions import db, bcrypt


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user_medicines = db.relationship('UserMedicine', backref='user', lazy=True)
    reminders = db.relationship('MedicationReminder', backref='user', cascade='all, delete-orphan')

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


class Medicine(db.Model):
    
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user_medicines = db.relationship('UserMedicine', backref='medicine', lazy=True)

    def __repr__(self):
        return f"<Medicine {self.name}>"


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

    reminders = db.relationship('MedicationReminder', backref='user_medicine', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<UserMedicine User: {self.user_id}, Medicine: {self.medicine_id}>"


class MedicationReminder(db.Model):

    __tablename__ = 'medication_reminders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_medicine_id = db.Column(db.Integer, db.ForeignKey('user_medicines.id', ondelete='CASCADE'), nullable=False)
    reminder_time = db.Column(db.Time, nullable=False)
    reminder_message = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum('pending', 'sent', name='reminder_status'), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_user_medicine_id', 'user_medicine_id'),
        db.Index('idx_reminder_time', 'reminder_time'),
    )

    def __repr__(self):
        return f"<MedicationReminder User: {self.user_id}, Medicine: {self.user_medicine_id}, Time: {self.reminder_time}, Status: {self.status}>"