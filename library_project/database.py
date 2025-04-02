# # database.py
# import sqlite3
# from datetime import datetime, timedelta

# def init_db():
#     conn = sqlite3.connect('library.db')
#     cursor = conn.cursor()

#     # Create tables

    
#     # Item Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Item (
#             ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Title TEXT NOT NULL,
#             Type TEXT NOT NULL,
#             Author TEXT,
#             PublicationDate TEXT,
#             Genre TEXT
#         )
#     ''')

#     # Copy Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Copy (
#             CopyID INTEGER PRIMARY KEY AUTOINCREMENT,
#             ItemID INTEGER NOT NULL,
#             Condition TEXT,
#             Availability INTEGER NOT NULL DEFAULT 1,
#             FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
#         )
#     ''')

#     # User Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS User (
#             UserID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Name TEXT NOT NULL,
#             ContactInfo TEXT,
#             MembershipID TEXT NOT NULL UNIQUE,
#             TotalFines REAL DEFAULT 0.0,
#             IsVolunteer INTEGER DEFAULT 0
#         )
#     ''')

#     # SocialRoom Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS SocialRoom (
#             RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Name TEXT NOT NULL,
#             Capacity INTEGER NOT NULL
#         )
#     ''')

#     # Event Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Event (
#             EventID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Name TEXT NOT NULL,
#             Date TEXT NOT NULL,
#             Time TEXT,
#             Description TEXT,
#             RecommendedAudience TEXT,
#             RoomID INTEGER NOT NULL,
#             FOREIGN KEY (RoomID) REFERENCES SocialRoom(RoomID)
#         )
#     ''')

#     # Personnel Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Personnel (
#             PersonnelID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Name TEXT NOT NULL,
#             Position TEXT NOT NULL,
#             ContactInfo TEXT
#         )
#     ''')

#     # FutureItem Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS FutureItem (
#             FutureItemID INTEGER PRIMARY KEY AUTOINCREMENT,
#             Title TEXT NOT NULL,
#             Author TEXT,
#             Type TEXT NOT NULL,
#             ExpectedArrivalDate TEXT
#         )
#     ''')

#     # Borrows Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Borrows (
#             UserID INTEGER NOT NULL,
#             CopyID INTEGER NOT NULL,
#             BorrowDate TEXT NOT NULL,
#             DueDate TEXT NOT NULL,
#             ReturnDate TEXT,
#             PRIMARY KEY (UserID, CopyID, BorrowDate),
#             FOREIGN KEY (UserID) REFERENCES User(UserID),
#             FOREIGN KEY (CopyID) REFERENCES Copy(CopyID)
#         )
#     ''')

#     # Attends Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS Attends (
#             UserID INTEGER NOT NULL,
#             EventID INTEGER NOT NULL,
#             PRIMARY KEY (UserID, EventID),
#             FOREIGN KEY (UserID) REFERENCES User(UserID),
#             FOREIGN KEY (EventID) REFERENCES Event(EventID)
#         )
#     ''')

#     # ManagesEvent Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS ManagesEvent (
#             PersonnelID INTEGER NOT NULL,
#             EventID INTEGER NOT NULL,
#             PRIMARY KEY (PersonnelID, EventID),
#             FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID),
#             FOREIGN KEY (EventID) REFERENCES Event(EventID)
#         )
#     ''')

#     # ManagesItem Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS ManagesItem (
#             PersonnelID INTEGER NOT NULL,
#             ItemID INTEGER NOT NULL,
#             PRIMARY KEY (PersonnelID, ItemID),
#             FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID),
#             FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
#         )
#     ''')

#     # RecommendedFor Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS RecommendedFor (
#             ItemID INTEGER NOT NULL,
#             EventID INTEGER NOT NULL,
#             PRIMARY KEY (ItemID, EventID),
#             FOREIGN KEY (ItemID) REFERENCES Item(ItemID),
#             FOREIGN KEY (EventID) REFERENCES Event(EventID)
#         )
#     ''')

#     # HelpRequest Table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS HelpRequest (
#             RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
#             UserID INTEGER NOT NULL,
#             PersonnelID INTEGER NOT NULL,
#             RequestDate TEXT NOT NULL,
#             Issue TEXT NOT NULL,
#             Status TEXT NOT NULL,
#             FOREIGN KEY (UserID) REFERENCES User(UserID),
#             FOREIGN KEY (PersonnelID) REFERENCES Personnel(PersonnelID)
#         )
#     ''')


#     # Create Triggers
#     # Trigger 1: Set Availability to 0 when a copy is borrowed (INSERT into Borrows)
#     cursor.execute('''
#         CREATE TRIGGER IF NOT EXISTS set_availability_on_borrow
#         AFTER INSERT ON Borrows
#         WHEN NEW.ReturnDate IS NULL
#         BEGIN
#             UPDATE Copy
#             SET Availability = 0
#             WHERE CopyID = NEW.CopyID;
#         END;
#     ''')

#     # Trigger 2: Set Availability to 1 when a copy is returned (UPDATE on Borrows)
#     cursor.execute('''
#         CREATE TRIGGER IF NOT EXISTS set_availability_on_return
#         AFTER UPDATE OF ReturnDate ON Borrows
#         WHEN NEW.ReturnDate IS NOT NULL AND OLD.ReturnDate IS NULL
#         BEGIN
#             UPDATE Copy
#             SET Availability = 1
#             WHERE CopyID = NEW.CopyID;
#         END;
#     ''')

#     # Trigger 3: Recalculate TotalFines after a new borrow (INSERT into Borrows)
#     cursor.execute('''
#         CREATE TRIGGER IF NOT EXISTS update_fines_on_borrow
#         AFTER INSERT ON Borrows
#         BEGIN
#             UPDATE User
#             SET TotalFines = (
#                 SELECT COALESCE(SUM(
#                     (julianday('now') - julianday(DueDate)) * 0.50
#                 ), 0)
#                 FROM Borrows
#                 WHERE UserID = NEW.UserID
#                 AND ReturnDate IS NULL
#                 AND julianday('now') > julianday(DueDate)
#             )
#             WHERE UserID = NEW.UserID;
#         END;
#     ''')

#     # Trigger 4: Recalculate TotalFines after a return (UPDATE on Borrows)
#     cursor.execute('''
#         CREATE TRIGGER IF NOT EXISTS update_fines_on_return
#         AFTER UPDATE OF ReturnDate ON Borrows
#         WHEN NEW.ReturnDate IS NOT NULL AND OLD.ReturnDate IS NULL
#         BEGIN
#             UPDATE User
#             SET TotalFines = (
#                 SELECT COALESCE(SUM(
#                     (julianday('now') - julianday(DueDate)) * 0.50
#                 ), 0)
#                 FROM Borrows
#                 WHERE UserID = NEW.UserID
#                 AND ReturnDate IS NULL
#                 AND julianday('now') > julianday(DueDate)
#             )
#             WHERE UserID = NEW.UserID;
#         END;
#     ''')

#     # Insert sample data
#     # Items
#     cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
#                    (1, "To Kill a Mockingbird", "PrintBook", "Harper Lee", "1960-07-11", "Fiction"))
#     cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
#                    (2, "1984", "PrintBook", "George Orwell", "1949-06-08", "Dystopia"))

#     # Copies
#     cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
#                    (1, 1, "New", 1))
#     cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
#                    (2, 1, "Good", 1))
#     cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
#                    (3, 2, "Worn", 1))

#     # Users
#     cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
#                    (1, "Alice Smith", "alice@email.com", "M001", 0.0, 0))
#     cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
#                    (2, "Bob Johnson", "bob@email.com", "M002", 0.0, 0))

#     # SocialRoom
#     cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
#                    (1, "Reading Room", 20))

#     # Event
#     cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                    (1, "Mystery Book Club", "2025-04-10", "18:00", "Discuss mystery novels", "Adults", 1))

#     # Personnel
#     cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
#                    (1, "Jane Doe", "Librarian", "jane@email.com"))

#     # FutureItem
#     cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
#                    (1, "New Novel", "John Smith", "PrintBook", "2025-05-01"))

#     # Commit and close
#     conn.commit()
#     conn.close()

# if __name__ == "__main__":
#     init_db()






















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
    # Items (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (1, 'To Kill a Mockingbird', 'PrintBook', 'Harper Lee', '1960-07-11', 'Fiction'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (2, '1984', 'PrintBook', 'George Orwell', '1949-06-08', 'Dystopia'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (3, 'National Geographic', 'Magazine', 'Various', '2023-10-01', 'Science'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (4, 'Nature', 'Journal', 'Various', '2023-09-15', 'Scientific'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (5, 'Abbey Road', 'CD', 'The Beatles', '1969-09-26', 'Rock'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (6, 'Dark Side of the Moon', 'Record', 'Pink Floyd', '1973-03-01', 'Rock'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (7, 'Digital Fortress', 'OnlineBook', 'Dan Brown', '1998-01-01', 'Thriller'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (8, 'The Innovators', 'OnlineBook', 'Walter Isaacson', '2014-10-07', 'Technology'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (9, 'Time', 'Magazine', 'Various', '2023-11-01', 'News'))
    cursor.execute("INSERT OR IGNORE INTO Item (ItemID, Title, Type, Author, PublicationDate, Genre) VALUES (?, ?, ?, ?, ?, ?)",
                   (10, 'Thriller', 'CD', 'Michael Jackson', '1982-11-30', 'Pop'))

    # Copies (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (1, 1, 'New', 1))  # To Kill a Mockingbird
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (2, 1, 'Good', 1))  # To Kill a Mockingbird
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (3, 2, 'Worn', 0))  # 1984
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (4, 2, 'Good', 1))  # 1984
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (5, 3, 'New', 1))  # National Geographic
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (6, 4, 'Good', 1))  # Nature
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (7, 5, 'New', 1))  # Abbey Road
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (8, 6, 'Worn', 1))  # Dark Side of the Moon
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (9, 7, 'New', 1))  # Digital Fortress
    cursor.execute("INSERT OR IGNORE INTO Copy (CopyID, ItemID, Condition, Availability) VALUES (?, ?, ?, ?)",
                   (10, 8, 'New', 1))  # The Innovators

    # Users (10 tuples) - TotalFines set to 0 since it will be calculated by the trigger
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (1, 'Alice Smith', 'alice@email.com', 'M001', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (2, 'Bob Johnson', 'bob@email.com', 'M002', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (3, 'Carol Lee', 'carol@email.com', 'M003', 0, 1))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (4, 'Dave Brown', 'dave@email.com', 'M004', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (5, 'Eve White', 'eve@email.com', 'M005', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (6, 'Frank Green', 'frank@email.com', 'M006', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (7, 'Grace Kim', 'grace@email.com', 'M007', 0, 1))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (8, 'Hank Patel', 'hank@email.com', 'M008', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (9, 'Ivy Chen', 'ivy@email.com', 'M009', 0, 0))
    cursor.execute("INSERT OR IGNORE INTO User (UserID, Name, ContactInfo, MembershipID, TotalFines, IsVolunteer) VALUES (?, ?, ?, ?, ?, ?)",
                   (10, 'Jack Black', 'jack@email.com', 'M010', 0, 0))

    # SocialRoom (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (1, 'Main Hall', 50))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (2, 'Reading Room', 20))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (3, 'Conference Room', 30))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (4, 'Art Gallery', 40))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (5, 'Media Room', 25))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (6, 'Kids Corner', 15))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (7, 'Study Room A', 10))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (8, 'Study Room B', 10))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (9, 'Event Space', 60))
    cursor.execute("INSERT OR IGNORE INTO SocialRoom (RoomID, Name, Capacity) VALUES (?, ?, ?)",
                   (10, 'Lounge', 35))

    # Event (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (1, 'Mystery Book Club', '2023-12-01', '18:00', 'Discuss mystery novels', 'Adults', 1))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (2, 'Local Art Show', '2023-12-05', '14:00', 'Showcase local artists', 'All Ages', 4))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (3, 'Classic Film Night', '2023-12-10', '19:00', 'Screening of classics', 'Adults', 5))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (4, 'Kids Story Time', '2023-12-15', '10:00', 'Stories for kids', 'Kids', 6))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (5, 'Sci-Fi Book Club', '2023-12-20', '17:00', 'Sci-fi discussions', 'Teens', 2))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (6, 'Music History Talk', '2023-12-25', '15:00', 'History of rock music', 'Adults', 3))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (7, 'Poetry Reading', '2023-12-30', '16:00', 'Local poets', 'All Ages', 7))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (8, 'Tech Talk', '2024-01-05', '18:00', 'Tech innovations', 'Adults', 8))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (9, 'Craft Workshop', '2024-01-10', '13:00', 'DIY crafts', 'Kids', 9))
    cursor.execute("INSERT OR IGNORE INTO Event (EventID, Name, Date, Time, Description, RecommendedAudience, RoomID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (10, 'Film Discussion', '2024-01-15', '19:00', 'Discuss recent films', 'Teens', 10))

    # Personnel (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (1, 'Lisa Wong', 'Librarian', 'lisa@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (2, 'Mark Evans', 'Assistant', 'mark@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (3, 'Sara Kim', 'Manager', 'sara@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (4, 'Tom Reed', 'Librarian', 'tom@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (5, 'Nina Patel', 'Assistant', 'nina@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (6, 'Omar Ali', 'Technician', 'omar@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (7, 'Pia Gupta', 'Librarian', 'pia@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (8, 'Quinn Lee', 'Assistant', 'quinn@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (9, 'Rita Diaz', 'Event Coordinator', 'rita@library.org'))
    cursor.execute("INSERT OR IGNORE INTO Personnel (PersonnelID, Name, Position, ContactInfo) VALUES (?, ?, ?, ?)",
                   (10, 'Sam Cole', 'Librarian', 'sam@library.org'))

    # FutureItem (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (1, 'New Novel', 'Jane Doe', 'PrintBook', '2024-03-01'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (2, 'Tech Mag', 'Various', 'Magazine', '2024-02-15'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (3, 'Jazz CD', 'Miles Davis', 'CD', '2024-04-01'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (4, 'Science Vol 10', 'Various', 'Journal', '2024-03-15'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (5, 'E-Book 2024', 'John Smith', 'OnlineBook', '2024-02-01'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (6, 'Rock Record', 'The Who', 'Record', '2024-05-01'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (7, 'Kids Book', 'Ann Lee', 'PrintBook', '2024-03-10'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (8, 'News Mag', 'Various', 'Magazine', '2024-02-20'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (9, 'Pop CD', 'Adele', 'CD', '2024-04-15'))
    cursor.execute("INSERT OR IGNORE INTO FutureItem (FutureItemID, Title, Author, Type, ExpectedArrivalDate) VALUES (?, ?, ?, ?, ?)",
                   (10, 'Bio Journal', 'Various', 'Journal', '2024-03-25'))

    # Borrows (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (1, 1, '2023-11-01', '2023-11-15', '2023-11-10'))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (2, 3, '2023-11-05', '2023-11-19', None))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (3, 2, '2023-11-10', '2023-11-24', '2023-11-20'))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (4, 4, '2023-11-15', '2023-11-29', None))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (5, 5, '2023-11-20', '2023-12-04', '2023-11-25'))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (6, 6, '2023-11-25', '2023-12-09', None))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (7, 7, '2023-11-30', '2023-12-14', '2023-12-01'))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (8, 8, '2023-12-01', '2023-12-15', None))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (9, 9, '2023-12-05', '2023-12-19', '2023-12-10'))
    cursor.execute("INSERT OR IGNORE INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?)",
                   (10, 10, '2023-12-10', '2023-12-24', None))

    # Attends (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (1, 1))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (2, 2))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (3, 3))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (4, 4))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (5, 5))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (6, 6))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (7, 7))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (8, 8))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (9, 9))
    cursor.execute("INSERT OR IGNORE INTO Attends (UserID, EventID) VALUES (?, ?)", (10, 10))

    # ManagesEvent (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (1, 1))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (2, 2))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (3, 3))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (4, 4))
    # ManagesEvent (remaining 6 tuples to complete 10)
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (5, 5))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (6, 6))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (7, 7))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (8, 8))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (9, 9))
    cursor.execute("INSERT OR IGNORE INTO ManagesEvent (PersonnelID, EventID) VALUES (?, ?)", (10, 10))

    # ManagesItem (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (1, 1))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (2, 2))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (3, 3))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (4, 4))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (5, 5))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (6, 6))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (7, 7))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (8, 8))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (9, 9))
    cursor.execute("INSERT OR IGNORE INTO ManagesItem (PersonnelID, ItemID) VALUES (?, ?)", (10, 10))

    # RecommendedFor (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (1, 1))  # To Kill a Mockingbird for Mystery Book Club
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (2, 5))  # 1984 for Sci-Fi Book Club
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (3, 8))  # National Geographic for Tech Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (4, 8))  # Nature for Tech Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (5, 6))  # Abbey Road for Music History Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (6, 6))  # Dark Side of the Moon for Music History Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (7, 1))  # Digital Fortress for Mystery Book Club
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (8, 8))  # The Innovators for Tech Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (9, 8))  # Time for Tech Talk
    cursor.execute("INSERT OR IGNORE INTO RecommendedFor (ItemID, EventID) VALUES (?, ?)", (10, 6)) # Thriller for Music History Talk

    # HelpRequest (10 tuples)
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (1, 1, 1, '2023-11-01', 'Cannot find book', 'Resolved'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (2, 2, 2, '2023-11-02', 'Issue with membership', 'Pending'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (3, 3, 3, '2023-11-03', 'Event registration issue', 'Resolved'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (4, 4, 4, '2023-11-04', 'Cannot access online book', 'Pending'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (5, 5, 5, '2023-11-05', 'Lost item', 'Resolved'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (6, 6, 6, '2023-11-06', 'Technical issue with app', 'Pending'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (7, 7, 7, '2023-11-07', 'Request for book recommendation', 'Resolved'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (8, 8, 8, '2023-11-08', 'Issue with fine calculation', 'Pending'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (9, 9, 9, '2023-11-09', 'Event scheduling conflict', 'Resolved'))
    cursor.execute("INSERT OR IGNORE INTO HelpRequest (RequestID, UserID, PersonnelID, RequestDate, Issue, Status) VALUES (?, ?, ?, ?, ?, ?)",
                   (10, 10, 10, '2023-11-10', 'Cannot return item', 'Pending'))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()






