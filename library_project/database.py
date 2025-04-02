# database.py
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()

    # Create tables

    
    # Item Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Item (
            ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Type TEXT NOT NULL,
            Author TEXT,
            PublicationDate TEXT,
            Genre TEXT
        )
    ''')

    # Copy Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Copy (
            CopyID INTEGER PRIMARY KEY AUTOINCREMENT,
            ItemID INTEGER NOT NULL,
            Condition TEXT,
            Availability INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
        )
    ''')

    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            ContactInfo TEXT,
            MembershipID TEXT NOT NULL UNIQUE,
            TotalFines REAL DEFAULT 0.0,
            IsVolunteer INTEGER DEFAULT 0
        )
    ''')

    # SocialRoom Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SocialRoom (
            RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Capacity INTEGER NOT NULL
        )
    ''')

    # Event Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Event (
            EventID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Date TEXT NOT NULL,
            Time TEXT,
            Description TEXT,
            RecommendedAudience TEXT,
            RoomID INTEGER NOT NULL,
            FOREIGN KEY (RoomID) REFERENCES SocialRoom(RoomID)
        )
    ''')

    # Personnel Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Personnel (
            PersonnelID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Position TEXT NOT NULL,
            ContactInfo TEXT
        )
    ''')

    # FutureItem Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS FutureItem (
            FutureItemID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Author TEXT,
            Type TEXT NOT NULL,
            ExpectedArrivalDate TEXT
        )
    ''')

    # Borrows Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Borrows (
            UserID INTEGER NOT NULL,
            CopyID INTEGER NOT NULL,
            BorrowDate TEXT NOT NULL,
            DueDate TEXT NOT NULL,
            ReturnDate TEXT,
            PRIMARY KEY (UserID, CopyID, BorrowDate),
            FOREIGN KEY (UserID) REFERENCES User(UserID),
            FOREIGN KEY (CopyID) REFERENCES Copy(CopyID)
        )
    ''')

    # Attends Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attends (
            UserID INTEGER NOT NULL,
            EventID INTEGER NOT NULL,
            PRIMARY KEY (UserID, EventID),
            FOREIGN KEY (UserID) REFERENCES User(UserID),
            FOREIGN KEY (EventID) REFERENCES Event(EventID)
        )
    ''')

    # ManagesEvent Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ManagesEvent (
            PersonnelID INTEGER NOT NULL,
            EventID INTEGER NOT NULL,
            PRIMARY KEY (PersonnelID, EventID),
            FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID),
            FOREIGN KEY (EventID) REFERENCES Event(EventID)
        )
    ''')

    # ManagesItem Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ManagesItem (
            PersonnelID INTEGER NOT NULL,
            ItemID INTEGER NOT NULL,
            PRIMARY KEY (PersonnelID, ItemID),
            FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID),
            FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
        )
    ''')

    # RecommendedFor Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RecommendedFor (
            ItemID INTEGER NOT NULL,
            EventID INTEGER NOT NULL,
            PRIMARY KEY (ItemID, EventID),
            FOREIGN KEY (ItemID) REFERENCES Item(ItemID),
            FOREIGN KEY (EventID) REFERENCES Event(EventID)
        )
    ''')

    # HelpRequest Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS HelpRequest (
            RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER NOT NULL,
            PersonnelID INTEGER NOT NULL,
            RequestDate TEXT NOT NULL,
            Issue TEXT NOT NULL,
            Status TEXT NOT NULL,
            FOREIGN KEY (UserID) REFERENCES User(UserID),
            FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID)
        )
    ''')


    # Create Triggers
    # Trigger 1: Set Availability to 0 when a copy is borrowed (INSERT into Borrows)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS set_availability_on_borrow
        AFTER INSERT ON Borrows
        WHEN NEW.ReturnDate IS NULL
        BEGIN
            UPDATE Copy
            SET Availability = 0
            WHERE CopyID = NEW.CopyID;
        END;
    ''')

    # Trigger 2: Set Availability to 1 when a copy is returned (UPDATE on Borrows)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS set_availability_on_return
        AFTER UPDATE OF ReturnDate ON Borrows
        WHEN NEW.ReturnDate IS NOT NULL AND OLD.ReturnDate IS NULL
        BEGIN
            UPDATE Copy
            SET Availability = 1
            WHERE CopyID = NEW.CopyID;
        END;
    ''')

    # Trigger 3: Recalculate TotalFines after a new borrow (INSERT into Borrows)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_fines_on_borrow
        AFTER INSERT ON Borrows
        BEGIN
            UPDATE User
            SET TotalFines = (
                SELECT COALESCE(SUM(
                    (julianday('now') - julianday(DueDate)) * 0.50
                ), 0)
                FROM Borrows
                WHERE UserID = NEW.UserID
                AND ReturnDate IS NULL
                AND julianday('now') > julianday(DueDate)
            )
            WHERE UserID = NEW.UserID;
        END;
    ''')

    # Trigger 4: Recalculate TotalFines after a return (UPDATE on Borrows)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_fines_on_return
        AFTER UPDATE OF ReturnDate ON Borrows
        WHEN NEW.ReturnDate IS NOT NULL AND OLD.ReturnDate IS NULL
        BEGIN
            UPDATE User
            SET TotalFines = (
                SELECT COALESCE(SUM(
                    (julianday('now') - julianday(DueDate)) * 0.50
                ), 0)
                FROM Borrows
                WHERE UserID = NEW.UserID
                AND ReturnDate IS NULL
                AND julianday('now') > julianday(DueDate)
            )
            WHERE UserID = NEW.UserID;
        END;
    ''')

    # Insert sample data
    # Items
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (1, "To Kill a Mockingbird", "PrintBook", "Harper Lee", "1960-07-11", "Fiction"))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (2, "1984", "PrintBook", "George Orwell", "1949-06-08", "Dystopia"))

    # Copies
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (1, 1, "New", 1))
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (2, 1, "Good", 1))
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (3, 2, "Worn", 1))

    # Users
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (1, "Alice Smith", "alice@email.com", "M001", 0.0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (2, "Bob Johnson", "bob@email.com", "M002", 0.0, 0))

    # SocialRoom
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (1, "Reading Room", 20))

    # Event
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (1, "Mystery Book Club", "2025-04-10", "18:00", "Discuss mystery novels", "Adults", 1))

    # Personnel
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (1, "Jane Doe", "Librarian", "jane@email.com"))

    # FutureItem
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (1, "New Novel", "John Smith", "PrintBook", "2025-05-01"))

    # Commit and close
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()











