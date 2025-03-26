"""
models.py
---------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/models.py

Purpose:    Contains the database models for the Flask application, including User, Medicine, UserMedicine, 
            and MedicationReminder models, and their relationships.
"""


from app.extensions import db, bcrypt


class User(db.Model):
    """
    Represents a User entity in the database.

    This model represents a user in the system, containing essential information
    such as email, password, and phone number. It also stores user-specific preferences,
    such as receiving SMS reminders. The User model supports relationships with
    other models, including medication associations and medication reminders.

    Attributes:
        id (int): The unique identifier for the user.
        email (str): The user's email address. This is unique and used for authentication.
        password_hash (str): The hashed password of the user for secure authentication.
        phone_number (str): The user's phone number. This is unique and optional.
        receive_sms_reminders (bool): Indicates whether the user wants to receive SMS reminders.
        created_at (datetime): Timestamp of when the user was created.
        updated_at (datetime): Timestamp of when the user was last updated.

    Relationships:
        user_medicines (list): A list of UserMedicine records representing medications associated with the user.
        reminders (list): A list of MedicationReminder records associated with the user, used for scheduling reminders.

    Methods:
        is_active(): Returns True, indicating the user is active.
        is_authenticated(): Returns True, indicating the user is authenticated.
        is_anonymous(): Returns False, indicating the user is not anonymous.
        get_id(): Returns the string representation of the user's ID.
        check_password(password): Checks if the provided password matches the user's stored password hash.
        set_password(password): Sets the user's password after hashing it.
        __repr__(): Returns a string representation of the User object, primarily the user's email.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    receive_sms_reminders = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    user_medicines = db.relationship("UserMedicine", backref="user", lazy=True)
    reminders = db.relationship(
        "MedicationReminder", backref="user", cascade="all, delete-orphan"
    )

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
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def __repr__(self):
        return f"<User {self.email}>"


class Medicine(db.Model):
    """
    Represents a Medicine entity in the database.

    This model represents a medicine record in the database, including essential information
    such as the medicine's name and timestamps for when it was created and last updated. The
    model supports a one-to-many relationship with the UserMedicine model, which tracks the
    medicines associated with specific users.

    Attributes:
        id (int): The unique identifier for the medicine.
        name (str): The name of the medicine.
        created_at (datetime): Timestamp of when the medicine record was created.
        updated_at (datetime): Timestamp of when the medicine record was last updated.

    Relationships:
        user_medicines (list): A list of UserMedicine records representing the association of
                                this medicine with specific users.

    Methods:
        __repr__(): Returns a string representation of the Medicine object, primarily the medicine's name.
    """

    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    user_medicines = db.relationship("UserMedicine", backref="medicine", lazy=True)

    def __repr__(self):
        return f"<Medicine {self.name}>"


class UserMedicine(db.Model):
    """
    Represents the association between a User and a Medicine in the database.

    This model tracks the association of a user with a specific medicine, including dosage,
    frequency, and any notes related to the medication. It also includes timestamps for
    when the association was created and last updated. The model supports a one-to-many
    relationship with the MedicationReminder model, which allows for setting reminders
    for the user regarding this medicine.

    Attributes:
        id (int): The unique identifier for the user-medicine association.
        user_id (int): The foreign key reference to the User model, indicating which user is associated with the medicine.
        medicine_id (int): The foreign key reference to the Medicine model, indicating which medicine is associated with the user.
        dosage (str): The dosage amount for the user to take.
        frequency (str): The frequency at which the user should take the medicine (e.g., daily, twice a day).
        notes (str): Any additional notes or instructions related to the user’s medicine regimen.
        created_at (datetime): Timestamp of when the user-medicine association was created.
        updated_at (datetime): Timestamp of when the user-medicine association was last updated.

    Relationships:
        reminders (list): A list of MedicationReminder records that are associated with this user-medicine pair.

    Methods:
        __repr__(): Returns a string representation of the UserMedicine object, showing the associated user and medicine.
    """

    __tablename__ = "user_medicines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    dosage = db.Column(db.String(255), nullable=False)
    frequency = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    reminders = db.relationship(
        "MedicationReminder", backref="user_medicine", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserMedicine User: {self.user_id}, Medicine: {self.medicine_id}>"


class MedicationReminder(db.Model):
    """
    Represents a Medication Reminder entity in the database.

    This model represents a reminder for a user to take their medicine at a specific time.
    The reminder includes details such as the time for the reminder, an optional message,
    and the status of the reminder (e.g., pending or sent). This model also includes timestamps
    for when the reminder was created and last updated.

    Attributes:
        id (int): The unique identifier for the medication reminder.
        user_id (int): The foreign key reference to the User model, indicating which user the reminder is for.
        user_medicine_id (int): The foreign key reference to the UserMedicine model, indicating which user-medicine association the reminder is for.
        reminder_time (time): The time of day when the reminder should trigger.
        reminder_message (str): An optional message to include with the reminder.
        status (str): The current status of the reminder, such as 'pending' or 'sent'.
        created_at (datetime): Timestamp of when the reminder was created.
        updated_at (datetime): Timestamp of when the reminder was last updated.

    Relationships:
        user (User): The user associated with this reminder, via the user_id foreign key.
        user_medicine (UserMedicine): The user-medicine association related to this reminder, via the user_medicine_id foreign key.

    Indexes:
        idx_user_id (Index): Index on the user_id column for faster lookups.
        idx_user_medicine_id (Index): Index on the user_medicine_id column for faster lookups.
        idx_reminder_time (Index): Index on the reminder_time column for faster query performance by reminder time.

    Methods:
        __repr__(): Returns a string representation of the MedicationReminder object, showing the user, medicine, reminder time, and status.
    """

    __tablename__ = "medication_reminders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_medicine_id = db.Column(
        db.Integer,
        db.ForeignKey("user_medicines.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminder_time = db.Column(db.Time, nullable=False)
    reminder_message = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.Enum("pending", "sent", name="reminder_status"), default="pending"
    )
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.Index("idx_user_id", "user_id"),
        db.Index("idx_user_medicine_id", "user_medicine_id"),
        db.Index("idx_reminder_time", "reminder_time"),
    )

    def __repr__(self):
        return f"<MedicationReminder User: {self.user_id}, Medicine: {self.user_medicine_id}, Time: {self.reminder_time}, Status: {self.status}>"
