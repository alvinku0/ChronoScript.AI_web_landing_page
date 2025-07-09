from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Initialize SQLAlchemy
db = SQLAlchemy()

# SQLite WAL mode configuration
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for WAL mode and optimal performance"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set synchronous mode to NORMAL for better performance with WAL
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Set cache size for better performance (negative value = KB)
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set timeout for busy database (30 seconds)
        cursor.execute("PRAGMA busy_timeout=30000")
        # Optimize for better performance
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
        cursor.close()

class Contact(db.Model):
    """Contact form submission model"""
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    
    def __repr__(self):
        return f'<Contact {self.id}: {self.first_name} {self.last_name or ""} - {self.email}>'
    
    def to_dict(self):
        """Convert contact to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'company_name': self.company_name,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address
        }
    
    @classmethod
    def create_contact(cls, first_name, last_name, email, company_name, message, ip_address=None):
        """Create a new contact form submission"""
        contact = cls(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company_name=company_name,
            message=message,
            ip_address=ip_address
        )
        db.session.add(contact)
        db.session.commit()
        return contact
    
    @classmethod
    def get_all_contacts(cls):
        """Retrieve all contact submissions ordered by most recent first"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_contact_by_id(cls, contact_id):
        """Retrieve a specific contact by ID"""
        return cls.query.get(contact_id)
    
    @classmethod
    def get_contacts_by_email(cls, email):
        """Retrieve all contacts with a specific email"""
        return cls.query.filter_by(email=email).order_by(cls.created_at.desc()).all()

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database initialized successfully with SQLAlchemy.")

def get_db():
    """Get the database instance"""
    return db
