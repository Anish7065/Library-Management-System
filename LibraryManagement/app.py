import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db import get_connection, init_db
# INITIALIZATION
init_db()

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Library Management System")

# NAVIGATION

menu = [
    "Dashboard",
    "View Inventory",
    "Add New Book",
    "Manage Members",
    "Issue Book",
    "Return Book",
    "Borrowing History"
]

choice = st.sidebar.selectbox(
    "Navigation",
    menu
)


# for connecting to Database
conn = get_connection()

# Functions
# 1. DASHBOARD

if choice == "Dashboard":

    st.subheader("📊 System Overview")
    # TOTAL BOOK COPIES
    query = """
        SELECT COALESCE(SUM(total_copies), 0)
        FROM books
    """
    cursor = conn.cursor()
    cursor.execute(query)

    total_books = cursor.fetchone()[0]

    cursor.close()
    # AVAILABLE BOOK COPIES

    query = """
        SELECT COALESCE(SUM(available_copies), 0)
        FROM books
    """

    cursor = conn.cursor()
    cursor.execute(query)

    available_books = cursor.fetchone()[0]

    cursor.close()

    # ACTIVE LOANS
    query = """
        SELECT COUNT(*)
        FROM borrow_records
        WHERE return_date IS NULL
    """

    cursor = conn.cursor()
    cursor.execute(query)

    active_loans = cursor.fetchone()[0]

    cursor.close()

    # OVERDUE BOOKS

    query = """
        SELECT COUNT(*)
        FROM borrow_records
        WHERE return_date IS NULL
        AND due_date < CURDATE()
    """

    cursor = conn.cursor()
    cursor.execute(query)

    overdue_books = cursor.fetchone()[0]

    cursor.close()

    # DISPLAY METRICS

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Book Copies",
        total_books
    )

    col2.metric(
        "Available Copies",
        available_books
    )

    col3.metric(
        "Currently Issued",
        active_loans
    )

    col4.metric(
        "Overdue Books",
        overdue_books
    )

# 2. VIEW INVENTORY
elif choice == "View Inventory":

    st.subheader("📚 Current Catalog")


    search = st.text_input(
        "🔎 Search by title or author",
        placeholder="Enter title or author..."
    )


    if search.strip():

        query = """
            SELECT
                book_id,
                title,
                author,
                total_copies,
                available_copies
            FROM books
            WHERE title LIKE %s
               OR author LIKE %s
            ORDER BY title
        """

        df = pd.read_sql(
            query,
            conn,
            params=(
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:

        query = """
            SELECT
                book_id,
                title,
                author,
                total_copies,
                available_copies
            FROM books
            ORDER BY title
        """

        df = pd.read_sql(
            query,
            conn
        )


    if df.empty:

        st.info("No books found.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

# 3. ADD NEW BOOK
elif choice == "Add New Book":

    st.subheader("➕ Add Book to Catalog")


    with st.form("add_book_form"):

        title = st.text_input(
            "Book Title"
        )

        author = st.text_input(
            "Author"
        )

        copies = st.number_input(
            "Total Copies",
            min_value=1,
            step=1,
            value=1
        )


        submitted = st.form_submit_button(
            "Add Book"
        )


        if submitted:

            if not title.strip():

                st.error(
                    "Book title is required."
                )

            elif not author.strip():

                st.error(
                    "Author name is required."
                )

            else:

                query = """
                    INSERT INTO books
                    (
                        title,
                        author,
                        total_copies,
                        available_copies
                    )
                    VALUES (%s, %s, %s, %s)
                """

                cursor = conn.cursor()

                cursor.execute(
                    query,
                    (
                        title.strip(),
                        author.strip(),
                        copies,
                        copies
                    )
                )

                conn.commit()

                cursor.close()

                st.success(
                    f"Book '{title}' added successfully!"
                )


# 4. MANAGE MEMBERS
elif choice == "Manage Members":

    st.subheader("👤 Manage Library Members")


    tab1, tab2 = st.tabs(
        [
            "Add Member",
            "View Members"
        ]
    )

    # ADD MEMBER
    with tab1:

        with st.form("member_form"):

            name = st.text_input(
                "Member Name"
            )

            email = st.text_input(
                "Email"
            )

            phone = st.text_input(
                "Phone Number"
            )


            submitted = st.form_submit_button(
                "Add Member"
            )


            if submitted:

                if not name.strip():

                    st.error(
                        "Member name is required."
                    )

                else:

                    query = """
                        INSERT INTO members
                        (
                            name,
                            email,
                            phone
                        )
                        VALUES (%s, %s, %s)
                    """

                    cursor = conn.cursor()

                    cursor.execute(
                        query,
                        (
                            name.strip(),
                            email.strip(),
                            phone.strip()
                        )
                    )

                    conn.commit()

                    cursor.close()

                    st.success(
                        f"Member '{name}' added successfully!"
                    )

    # VIEW MEMBERS
    with tab2:

        query = """
            SELECT
                member_id,
                name,
                email,
                phone,
                created_at
            FROM members
            ORDER BY member_id DESC
        """

        members_df = pd.read_sql(
            query,
            conn
        )


        if members_df.empty:

            st.info(
                "No members registered yet."
            )

        else:

            st.dataframe(
                members_df,
                use_container_width=True,
                hide_index=True
            )

# 5. ISSUE BOOK
elif choice == "Issue Book":

    st.subheader("📖 Issue Book to Member")


    # GET AVAILABLE BOOKS

    books_query = """
        SELECT
            book_id,
            title,
            author,
            available_copies
        FROM books
        WHERE available_copies > 0
        ORDER BY title
    """

    available_books = pd.read_sql(
        books_query,
        conn
    )

    # GET MEMBERS

    members_query = """
        SELECT
            member_id,
            name
        FROM members
        ORDER BY name
    """

    members = pd.read_sql(
        members_query,
        conn
    )
    if available_books.empty:

        st.warning(
            "No books are currently available."
        )
    elif members.empty:
        st.warning(
            "No members found. Add a member first."
        )
    else:
        # BOOK SELECTION
        book_list = dict(
            zip(
                available_books["book_id"],
                available_books["title"]
            )
        )
        selected_book = st.selectbox(
            "Select Book",
            list(book_list.keys()),
            format_func=lambda x:
                f"{book_list[x]} (ID: {x})"
        )
        # MEMBER SELECTION
        member_list = dict(
            zip(
                members["member_id"],
                members["name"]
            )
        )
        selected_member = st.selectbox(
            "Select Member",
            list(member_list.keys()),
            format_func=lambda x:
                f"{member_list[x]} (ID: {x})"
        )
        # DUE DATE
        due_date = st.date_input(
            "Due Date",
            value=date.today() + timedelta(days=14),
            min_value=date.today()
        )
        if st.button("Issue Book"):
            cursor = conn.cursor()
            try:
                # CHECK AVAILABILITY
                cursor.execute(
                    """
                    SELECT available_copies
                    FROM books
                    WHERE book_id = %s
                    """,
                    (selected_book,)
                )

                result = cursor.fetchone()
                if result is None:
                    st.error(
                        "Book not found."
                    )
                    conn.rollback()
                elif result[0] <= 0:
                    st.error(
                        "This book is no longer available."
                    )
                    conn.rollback()
                else:
                    # DECREASE INVENTORY
                    cursor.execute(
                        """
                        UPDATE books
                        SET available_copies =
                            available_copies - 1
                        WHERE book_id = %s
                        """,
                        (selected_book,)
                    )
                    # CREATE BORROW RECORD
                    cursor.execute(
                        """
                        INSERT INTO borrow_records
                        (
                            member_id,
                            book_id,
                            due_date
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            selected_member,
                            selected_book,
                            due_date
                        )
                    )
                    conn.commit()
                    st.success(
                        f"Book issued to "
                        f"{member_list[selected_member]}!"
                    )
                    st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(
                    f"Error issuing book: {e}"
                )
            finally:

                cursor.close()
# 6. RETURN BOOK
elif choice == "Return Book":
    st.subheader("↩️ Process Book Return")
    # GET ACTIVE LOANS
    active_loans_query = """
        SELECT
            br.record_id,
            br.member_id,
            m.name AS member_name,
            br.book_id,
            b.title AS book_title,
            br.borrow_date,
            br.due_date

        FROM borrow_records br

        INNER JOIN members m
            ON br.member_id = m.member_id

        INNER JOIN books b
            ON br.book_id = b.book_id

        WHERE br.return_date IS NULL

        ORDER BY br.record_id DESC
    """
    active_df = pd.read_sql(
        active_loans_query,
        conn
    )
    if active_df.empty:

        st.info(
            "No active issued records found."
        )
    else:
        # CREATE SELECTION OPTIONS
        loan_options = {}
        for _, row in active_df.iterrows():
            loan_options[row["record_id"]] = (
                f"Record #{row['record_id']} | "
                f"{row['book_title']} | "
                f"{row['member_name']} | "
                f"Due: {row['due_date']}"
            )
        selected_record_id = st.selectbox(
            "Select Active Issue Record",
            list(loan_options.keys()),
            format_func=lambda x:
                loan_options[x]
        )
        selected_row = active_df[
            active_df["record_id"]
            == selected_record_id
        ].iloc[0]
        # CALCULATE FINE
        due_date = pd.to_datetime(
            selected_row["due_date"]
        ).date()
        today = date.today()
        overdue_days = max(
            0,
            (today - due_date).days
        )
        fine = overdue_days * 5
        if overdue_days > 0:
            st.warning(
                f"⚠️ This book is "
                f"{overdue_days} day(s) overdue."
            )
            st.info(
                f"Fine: ₹{fine}"
            )
        else:
            st.success(
                "Book is being returned on time."
            )
            st.info(
                "Fine: ₹0"
            )
        # Return Books
        if st.button("Process Return"):
            cursor = conn.cursor()
            try:
                # UPDATE BORROW RECORD
                cursor.execute(
                    """
                    UPDATE borrow_records

                    SET
                        return_date = CURRENT_TIMESTAMP,
                        fine = %s

                    WHERE record_id = %s
                    """,
                    (
                        fine,
                        selected_record_id
                    )
                )
                # RESTORE BOOK INVENTORY ,to increase the available copies of the book by 1
                cursor.execute(
                    """
                    UPDATE books
                    SET available_copies =
                        available_copies + 1
                    WHERE book_id = %s
                    """,
                    (
                        int(selected_row["book_id"]),
                    )
                )
                conn.commit()
                st.success(
                    f"Book returned successfully! "
                    f"Fine: ₹{fine}"
                )
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(
                    f"Error processing return: {e}"
                )
            finally:

                cursor.close()

# 7. BORROWING HISTORY
elif choice == "Borrowing History":
    st.subheader("📋 Borrowing History")
    query = """
        SELECT
            br.record_id,

            m.name AS member_name,

            b.title AS book_title,

            br.borrow_date,

            br.due_date,

            br.return_date,

            br.fine

        FROM borrow_records br

        INNER JOIN members m
            ON br.member_id = m.member_id

        INNER JOIN books b
            ON br.book_id = b.book_id

        ORDER BY br.record_id DESC
    """


    issued_df = pd.read_sql(
        query,
        conn
    )
    if issued_df.empty:
        st.info(
            "No borrowing records found."
        )
    else:
        st.dataframe(
            issued_df,
            use_container_width=True,
            hide_index=True
        )

conn.close()

