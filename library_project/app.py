# library_project/app.py


from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for flash messages

# Database connection helper with timeout and WAL mode
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('library.db', timeout=20)  # Increase timeout to 20 seconds
        g.db.row_factory = sqlite3.Row  # Allows accessing columns by name
        # Enable WAL mode for better concurrency
        g.db.execute("PRAGMA journal_mode=WAL;")
    return g.db

# Close the database connection at the end of each request
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.commit()  # Ensure any pending changes are committed
        db.close()

# Helper function to validate date format and logic
def validate_dates(borrow_date_str, due_date_str=None, return_date_str=None, borrow_date_ref=None):
    try:
        # Validate date format (YYYY-MM-DD)
        def parse_date(date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')

        # If borrow_date_ref is provided, parse it if it's a string
        if borrow_date_ref:
            if isinstance(borrow_date_ref, str):
                borrow_date = parse_date(borrow_date_ref)
            else:
                borrow_date = borrow_date_ref
        else:
            borrow_date = parse_date(borrow_date_str)

        if due_date_str:
            due_date = parse_date(due_date_str)
            if due_date <= borrow_date:
                return False, "Due date must be after borrow date."

        if return_date_str:
            return_date = parse_date(return_date_str)
            if return_date <= borrow_date:
                return False, "Return date must be after borrow date."

        return True, None
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD (e.g., 2025-04-02)."

# Application Logic: Borrow a Copy with Retry Logic
def borrow_copy(user_id, copy_id, borrow_date, due_date, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if the Copy is available
            cursor.execute("SELECT Availability FROM Copy WHERE CopyID = ?", (copy_id,))
            result = cursor.fetchone()
            
            if result is None:
                return False, "Copy does not exist."
            
            availability = result['Availability']
            
            if availability == 1:
                # Insert into Borrows (trigger will handle Availability and TotalFines updates)
                cursor.execute("""
                    INSERT INTO Borrows (UserID, CopyID, BorrowDate, DueDate, ReturnDate)
                    VALUES (?, ?, ?, ?, NULL)
                """, (user_id, copy_id, borrow_date, due_date))
                
                conn.commit()
                return True, "Copy borrowed successfully."
            else:
                return False, "Copy is not available."
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                logger.debug(f"Database locked during borrow, retrying... (attempt {attempt + 1}/{retries})")
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                logger.error(f"Failed to borrow CopyID {copy_id} for UserID {user_id}: {str(e)}")
                raise e

# Application Logic: Return a Copy
def return_copy(user_id, copy_id, return_date, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Log the attempt
            logger.debug(f"Attempting to return CopyID {copy_id} for UserID {user_id} on {return_date}")
            
            # Check if the borrowing exists and get the BorrowDate for validation
            cursor.execute("""
                SELECT * FROM Borrows
                WHERE UserID = ? AND CopyID = ? AND ReturnDate IS NULL
            """, (user_id, copy_id))
            borrow = cursor.fetchone()
            
            if not borrow:
                logger.debug(f"No active borrowing found for UserID {user_id} and CopyID {copy_id}")
                return False, "No active borrowing found."
            
            # Validate the return date against the borrow date
            borrow_date = borrow['BorrowDate']
            valid, error_message = validate_dates(borrow_date_str=None, return_date_str=return_date, borrow_date_ref=borrow_date)
            if not valid:
                return False, error_message
            
            # Update the Borrows table to set ReturnDate (trigger will handle Availability and TotalFines updates)
            cursor.execute("""
                UPDATE Borrows
                SET ReturnDate = ?
                WHERE UserID = ? AND CopyID = ? AND ReturnDate IS NULL
            """, (return_date, user_id, copy_id))
            
            if cursor.rowcount == 0:
                logger.debug(f"UPDATE affected 0 rows for UserID {user_id} and CopyID {copy_id}")
                return False, "No active borrowing found."
            
            logger.debug(f"Successfully returned CopyID {copy_id} for UserID {user_id}")
            conn.commit()
            return True, "Copy returned successfully."
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                logger.debug(f"Database locked during return, retrying... (attempt {attempt + 1}/{retries})")
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                logger.error(f"Failed to return CopyID {copy_id} for UserID {user_id}: {str(e)}")
                raise e

# Application Logic: Donate an Item
def donate_item(user_id, title, item_type, author, publication_date, genre, condition, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Insert the donated item into the Item table
            cursor.execute("""
                INSERT INTO Item (Title, Type, Author, PublicationDate, Genre)
                VALUES (?, ?, ?, ?, ?)
            """, (title, item_type, author, publication_date, genre))
            
            item_id = cursor.lastrowid  # Get the ID of the newly inserted item
            
            # Create a copy of the donated item
            cursor.execute("""
                INSERT INTO Copy (ItemID, Condition, Availability)
                VALUES (?, ?, 1)
            """, (item_id, condition))
            
            conn.commit()
            return True, f"Item '{title}' donated successfully by UserID {user_id}."
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise e

# Application Logic: Register for an Event
def register_event(user_id, event_id, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if the event exists
            cursor.execute("SELECT * FROM Event WHERE EventID = ?", (event_id,))
            event = cursor.fetchone()
            if not event:
                return False, "Event does not exist."
            
            # Check if the user is already registered
            cursor.execute("SELECT * FROM Attends WHERE UserID = ? AND EventID = ?", (user_id, event_id))
            if cursor.fetchone():
                return False, "You are already registered for this event."
            
            # Register the user for the event
            cursor.execute("""
                INSERT INTO Attends (UserID, EventID)
                VALUES (?, ?)
            """, (user_id, event_id))
            
            conn.commit()
            return True, "Successfully registered for the event."
        
        except sqlite3.IntegrityError:
            return False, "You are already registered for this event."
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise e

# Application Logic: Volunteer for the Library
def volunteer_for_library(user_id, wants_to_volunteer, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Update the user's IsVolunteer field
            is_volunteer = 1 if wants_to_volunteer.lower() == 'yes' else 0
            cursor.execute("""
                UPDATE User
                SET IsVolunteer = ?
                WHERE UserID = ?
            """, (is_volunteer, user_id))
            
            if cursor.rowcount == 0:
                return False, "User does not exist."
            
            conn.commit()
            return True, f"Volunteer status updated successfully for UserID {user_id}."
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise e

# Application Logic: Ask for Help from a Librarian
def ask_for_help(user_id, issue, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Find a librarian (Personnel) to assign the request to
            cursor.execute("SELECT PersonnelID FROM Personnel WHERE Position = 'Librarian' LIMIT 1")
            personnel = cursor.fetchone()
            personnel_id = personnel['PersonnelID'] if personnel else None
            
            if not personnel_id:
                return False, "No librarian available to handle the request."
            
            # Insert the help request
            cursor.execute("""
                INSERT INTO HelpRequest (UserID, PersonnelID, RequestDate, Issue, Status)
                VALUES (?, ?, ?, ?, 'Pending')
            """, (user_id, personnel_id, datetime.today().strftime('%Y-%m-%d'), issue))
            
            conn.commit()
            return True, "Help request submitted successfully."
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                import time
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise e

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    return render_template('users.html', users=users)

@app.route('/user/<int:user_id>')
def user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user details
    cursor.execute("SELECT * FROM User WHERE UserID = ?", (user_id,))
    user = cursor.fetchone()
    
    # Get borrowings
    cursor.execute("SELECT * FROM Borrows WHERE UserID = ?", (user_id,))
    borrows = cursor.fetchall()
    
    return render_template('user.html', user=user, borrows=borrows)

@app.route('/items')
def items():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all items and their copies
    cursor.execute("SELECT * FROM Item")
    items = cursor.fetchall()
    
    copies = {}
    for item in items:
        cursor.execute("SELECT * FROM Copy WHERE ItemID = ?", (item['ItemID'],))
        copies[item['ItemID']] = cursor.fetchall()
    
    return render_template('items.html', items=items, copies=copies)

@app.route('/borrow', methods=['GET', 'POST'])
def borrow():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users and copies for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM Copy")
    copies = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        copy_id = int(request.form['copy_id'])
        borrow_date = request.form['borrow_date']
        due_date = request.form['due_date']
        
        # Validate the dates
        valid, error_message = validate_dates(borrow_date, due_date)
        if not valid:
            flash(error_message, 'error')
            return render_template('borrow.html', users=users, copies=copies)
        
        success, message = borrow_copy(user_id, copy_id, borrow_date, due_date)
        if success:
            flash(message, 'success')
            # Refresh the copies list to reflect the updated availability
            cursor.execute("SELECT * FROM Copy")
            copies = cursor.fetchall()
        else:
            flash(message, 'error')
        
        return render_template('borrow.html', users=users, copies=copies)
    
    return render_template('borrow.html', users=users, copies=copies)

@app.route('/return', methods=['GET', 'POST'])
def return_copy_route():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users and active borrowings for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM Borrows WHERE ReturnDate IS NULL")
    borrows = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        copy_id = int(request.form['copy_id'])
        return_date = request.form['return_date']
        
        success, message = return_copy(user_id, copy_id, return_date)
        if success:
            flash(message, 'success')
            # Refresh the borrows list to reflect the updated state
            cursor.execute("SELECT * FROM Borrows WHERE ReturnDate IS NULL")
            borrows = cursor.fetchall()
        else:
            flash(message, 'error')
        
        return render_template('return.html', users=users, borrows=borrows)
    
    return render_template('return.html', users=users, borrows=borrows)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        title = request.form['title']
        item_type = request.form['item_type']
        author = request.form['author']
        publication_date = request.form['publication_date']
        genre = request.form['genre']
        condition = request.form['condition']
        
        success, message = donate_item(user_id, title, item_type, author, publication_date, genre, condition)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return render_template('donate.html', users=users)
    
    return render_template('donate.html', users=users)

@app.route('/events')
def events():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch all events
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    return render_template('events.html', events=events)

@app.route('/register_event', methods=['GET', 'POST'])
def register_event_route():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users and events for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        event_id = int(request.form['event_id'])
        
        success, message = register_event(user_id, event_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return render_template('register_event.html', users=users, events=events)
    
    return render_template('register_event.html', users=users, events=events)

@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        wants_to_volunteer = request.form['wants_to_volunteer']
        
        success, message = volunteer_for_library(user_id, wants_to_volunteer)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return render_template('volunteer.html', users=users)
    
    return render_template('volunteer.html', users=users)

@app.route('/ask_help', methods=['GET', 'POST'])
def ask_help():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch users for the form
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        issue = request.form['issue']
        
        success, message = ask_for_help(user_id, issue)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return render_template('ask_help.html', users=users)
    
    return render_template('ask_help.html', users=users)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, threaded=False)  # Disable reloader and multi-threading