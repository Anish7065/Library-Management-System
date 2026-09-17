import mysql.connector


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="use your_password_here",
        database="library_db"
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    # First connect without selecting a database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="use your_password_here",
    )

    cursor = conn.cursor()

    # Create database
    cursor.execute(
        """
        CREATE DATABASE IF NOT EXISTS library_db
        """
    )

    cursor.close()
    conn.close()

    # Connect to the library database
    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # BOOKS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (

            book_id INT AUTO_INCREMENT PRIMARY KEY,

            title VARCHAR(255) NOT NULL,

            author VARCHAR(255) NOT NULL,

            total_copies INT NOT NULL,

            available_copies INT NOT NULL,

            CHECK (total_copies >= 0),

            CHECK (available_copies >= 0),

            CHECK (available_copies <= total_copies)
        )
        """
    )


    # --------------------------------------------------------
    # MEMBERS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS members (

            member_id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(255) NOT NULL,

            email VARCHAR(255),

            phone VARCHAR(20),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # --------------------------------------------------------
    # BORROW RECORDS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS borrow_records (

            record_id INT AUTO_INCREMENT PRIMARY KEY,

            member_id INT NOT NULL,

            book_id INT NOT NULL,

            borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            due_date DATE NOT NULL,

            return_date TIMESTAMP NULL,

            fine DECIMAL(10,2) DEFAULT 0,

            FOREIGN KEY (member_id)
                REFERENCES members(member_id),

            FOREIGN KEY (book_id)
                REFERENCES books(book_id)
        )
        """
    )


    conn.commit()

    cursor.close()
    conn.close()

