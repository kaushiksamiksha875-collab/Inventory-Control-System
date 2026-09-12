from flask import Flask, request, redirect, flash, session
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key="inventory-secret-key"

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
    )
@app.route("/")
def home():
    return redirect("/login")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, name, password_hash
            FROM users
            WHERE email = %s
        """, (email,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and password == user[2]:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/dashboard")

        return """
        <h2>Invalid Login</h2>
        <p>Incorrect email or password.</p>
        <a href="/login">Try Again</a>
        """

    return """
    <html>
    <head>
        <title>Login - Inventory Control System</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f6f8;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }

            .login-box {
                background: white;
                padding: 30px;
                width: 350px;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }

            h2 {
                text-align: center;
            }

            input {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                box-sizing: border-box;
            }

            button {
                width: 100%;
                padding: 10px;
                background: #333;
                color: white;
                border: none;
                cursor: pointer;
            }
        </style>
    </head>

    <body>
        <div class="login-box">
            <h2>Inventory Control System</h2>

            <form method="POST">
                <input type="email" name="email" placeholder="Email" required>

                <input type="password" name="password" placeholder="Password" required>

                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/products", methods=["GET", "POST"])
def products():

    connection = get_db_connection()
    cursor = connection.cursor()

    # -----------------------------
    # ADD NEW PRODUCT
    # -----------------------------
    if request.method == "POST":

        product_name = request.form["product_name"]
        category_id = request.form["category_id"]
        supplier_id = request.form["supplier_id"]
        price = request.form["price"]
        quantity = request.form["quantity"]
        reorder_level = request.form["reorder_level"]

        cursor.execute("""
            INSERT INTO products
            (product_name, category_id, supplier_id, price, quantity, reorder_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            product_name,
            category_id,
            supplier_id,
            price,
            quantity,
            reorder_level
        ))

        connection.commit()
        flash("Product added successfully!")

    # -----------------------------
    # GET CATEGORIES
    # -----------------------------
    cursor.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    # -----------------------------
    # GET SUPPLIERS
    # -----------------------------
    cursor.execute("""
        SELECT supplier_id, supplier_name
        FROM suppliers
        ORDER BY supplier_name
    """)

    suppliers = cursor.fetchall()

    # -----------------------------
    # GET PRODUCTS WITH
    # CATEGORY + SUPPLIER NAMES
    # -----------------------------
    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    cursor.execute("""
        SELECT
            p.product_id,
            p.product_name,
            c.category_name,
            s.supplier_name,
            p.price,
            p.quantity,
            p.reorder_level
        FROM products p
        JOIN categories c
            ON p.category_id = c.category_id
        JOIN suppliers s
            ON p.supplier_id = s.supplier_id
        WHERE p.product_name ILIKE %s
AND (%s = '' OR p.category_id::text = %s)
       ORDER BY
    CASE
        WHEN p.quantity <= p.reorder_level THEN 0
        ELSE 1
    END,
    p.product_id;
   """, ('%' + search + '%', category_filter, category_filter))
    products = cursor.fetchall()
    category_options = ""
    for category in categories:
        selected = "selected" if str(category[0]) == category_filter else ""
        category_options += f'<option value="{category[0]}" {selected}>{category[1]}</option>'

    filter_form = f"""
            <form method="GET" action="/products" style="margin-bottom:20px;">
                <input type="text"
                       name="search"
                       placeholder="Search products..."
                       style="padding:10px; width:300px; border:1px solid #ccc; border-radius:6px;">

                <select name="category"
                        style="padding:10px; width:220px; border:1px solid #ccc; border-radius:6px; margin-left:10px;">
                    <option value="">All Categories</option>
                    {category_options}
                </select>

                <button type="submit"
                        style="padding:10px 18px; border:none; border-radius:6px; cursor:pointer; margin-left:10px;">
                    Filter
                </button>

                <a href="/products"
                   style="padding:10px 18px; margin-left:5px; text-decoration:none;">
                    Reset
                </a>
            </form>
    """

    cursor.close()
    connection.close()

    # -----------------------------
    # HTML
    # -----------------------------
    html = """
    <!DOCTYPE html>

    <html>

    <head>

        <title>Products</title>
        

        <style>

            body {
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                color: #333;
            }

            .navbar {
                background-color: #1f2937;
                padding: 18px 35px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .navbar h2 {
                margin: 0;
            }

            .navbar a {
                color: white;
                text-decoration: none;
                margin-left: 25px;
            }

            .container {
                padding: 35px;
            }

            .form-box {
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 600px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }

            label {
                display: block;
                margin-top: 15px;
                margin-bottom: 6px;
                font-weight: bold;
            }

            input,
            select {
                width: 100%;
                padding: 10px;
                box-sizing: border-box;
            }

            button {
                margin-top: 20px;
                padding: 12px 20px;
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }

            table {
                margin-top: 30px;
                width: 100%;
                border-collapse: collapse;
                background: white;
            }

            th,
            td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: left;
            }

            th {
                background-color: #1f2937;
                color: white;
            }

            .status-reorder {
                color: #dc2626;
                font-weight: bold;
            }

            .status-stock {
                color: #16a34a;
                font-weight: bold;
            }

            .action a {
                margin-right: 10px;
            }

        </style>

    </head>

    <body>

        <div class="navbar">

            <h2>Inventory Management System</h2>

            <div>

                <a href="/dashboard">Dashboard</a>
                <a href="/products">Products</a>
                <a href="/categories">Categories</a>
                <a href="/suppliers">Suppliers</a>
                <a href="/stock-transactions">Stock Transactions</a>

            </div>

        </div>


        <div class="container">

            <h1>Inventory Products</h1>


            <div class="form-box">

                <h2>Add New Product</h2>

                <form method="POST">

                    <label>Product Name</label>

                    <input
                        type="text"
                        name="product_name"
                        required
                    >


                    <label>Category</label>

                    <select name="category_id" required>

                        <option value="">
                            Select Category
                        </option>
    """

    # Add category options
    for category in categories:

        html += f"""
                        <option value="{category[0]}">
                            {category[1]}
                        </option>
        """

    html += """

                    </select>


                    <label>Supplier</label>

                    <select name="supplier_id" required>

                        <option value="">
                            Select Supplier
                        </option>
    """

    # Add supplier options
    for supplier in suppliers:

        html += f"""
                        <option value="{supplier[0]}">
                            {supplier[1]}
                        </option>
        """

    html += """

                    </select>


                    <label>Price</label>

                    <input
                        type="number"
                        step="0.01"
                        name="price"
                        required
                    >


                    <label>Quantity</label>

                    <input
                        type="number"
                        name="quantity"
                        min="0"
                        required
                    >


                    <label>Reorder Level</label>

                    <input
                        type="number"
                        name="reorder_level"
                        min="0"
                        required
                    >


                    <button type="submit">
                        Add Product
                    </button>

                </form>

            </div>

                    <h2>Product List</h2>
    """

    html += filter_form

    html += """
          
            <table>

                <tr>

                    <th>ID</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Supplier</th>
                    <th>Price</th>
                    <th>Quantity</th>
                    <th>Reorder Level</th>
                    <th>Status</th>
                    <th>Action</th>

                </tr>
    """

    # Add products to table
    for product in products:

        if product[5] <= product[6]:

            status = "Reorder"
            status_class = "status-reorder"

        else:

            status = "In Stock"
            status_class = "status-stock"


        html += f"""

                <tr>

                    <td>{product[0]}</td>

                    <td>{product[1]}</td>

                    <td>{product[2]}</td>

                    <td>{product[3]}</td>

                    <td>₹{product[4]}</td>

                    <td>{product[5]}</td>

                    <td>{product[6]}</td>

                    <td class="{status_class}">
                        {status}
                    </td>

                    <td class="action">

                        <a href="/view-product/{product[0]}">
                            View
                        </a>

                        <a href="/edit-product/{product[0]}">
                            Edit
                        </a>
<a href="/delete-product/{product[0]}"
   onclick="return confirm('Are you sure you want to delete this product?');">
    Delete
</a>
                        
                           
                        </a>

                    </td>

                </tr>

        """


    html += """

            </table>

        </div>

    </body>

    </html>

    """

    return html

@app.route("/categories", methods=["GET", "POST"])
def categories():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        category_name = request.form["category_name"]

        try:
            cur.execute(
                """
                INSERT INTO categories (category_name)
                VALUES (%s)
                """,
                (category_name,)
            )

            conn.commit()
            flash("Category added successfully!")

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Category already exists.")

        cur.close()
        conn.close()

        return redirect("/categories")

    # Get all categories
    cur.execute(
        """
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_id
        """
    )

    categories = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Categories</title>

        <style>

            body {
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                color: #333;
            }

            .navbar {
                background-color: #1f2937;
                padding: 18px 35px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .navbar h2 {
                margin: 0;
            }

            .navbar a {
                color: white;
                text-decoration: none;
                margin-left: 25px;
            }

            .container {
                padding: 35px;
            }

            .form-box {
                background: white;
                padding: 25px;
                border-radius: 10px;
                max-width: 500px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }

            label {
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 10px;
                box-sizing: border-box;
            }

            button {
                margin-top: 20px;
                padding: 12px 20px;
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }

            table {
                margin-top: 30px;
                width: 100%;
                max-width: 800px;
                border-collapse: collapse;
                background: white;
            }

            th, td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: left;
            }

            th {
                background-color: #1f2937;
                color: white;
            }

            .message {
                background-color: #e8f5e9;
                padding: 12px;
                margin-bottom: 20px;
                border-radius: 6px;
            }

        </style>

    </head>

    <body>

       <div class="navbar">
    <h2>Inventory Management System</h2>

    <div>
        <a href="/dashboard">Dashboard</a>
        <a href="/products">Products</a>
        <a href="/categories">Categories</a>
        <a href="/suppliers">Suppliers</a>
        <a href="/stock-transactions">Stock Transactions</a>
        <a href="/reports">Reports</a>
    </div>
</div>
        <div class="container">

            <h1>Categories</h1>

            

            <div class="form-box">

                <h2>Add New Category</h2>

                <form method="POST">

                    <label>Category Name</label>

                    <input
                        type="text"
                        name="category_name"
                        required
                    >

                    <button type="submit">
                        Add Category
                    </button>

                </form>

            </div>

            <h2>Category List</h2>

            <table>

                <tr>
    <th>ID</th>
    <th>Category Name</th>
    <th>Actions</th>
</tr>
    """

    for category in categories:

        html += f"""
               <tr>
    <td>{category[0]}</td>
    <td>{category[1]}</td>

    <td>
        <a href="/delete-category/{category[0]}"
           onclick="return confirm('Are you sure you want to delete this category?');">
            Delete
        </a>
    </td>
</tr>
        """

    html += """
            </table>

        </div>

    </body>

    </html>
    """

    return html
@app.route("/delete-category/<int:category_id>")
def delete_category(category_id):

    conn = get_db_connection()
    cur = conn.cursor()

    # Check whether category is being used by any product
    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE category_id = %s
    """, (category_id,))

    count = cur.fetchone()[0]

    # Do not delete category if products are using it
    if count > 0:
        cur.close()
        conn.close()

        flash("Cannot delete category because products are using it.")
        return redirect("/categories")

    # Delete category
    cur.execute("""
        DELETE FROM categories
        WHERE category_id = %s
    """, (category_id,))

    conn.commit()

    cur.close()
    conn.close()

    flash("Category deleted successfully!")

    return redirect("/categories")


@app.route("/suppliers", methods=["GET", "POST"])
def suppliers():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        supplier_name = request.form["supplier_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]

        cur.execute(
            """
            INSERT INTO suppliers
            (supplier_name, phone, email, address)
            VALUES (%s, %s, %s, %s)
            """,
            (supplier_name, phone, email, address)
        )

        conn.commit()
        flash("Supplier added successfully!")

        cur.close()
        conn.close()

        return redirect("/suppliers")

    # Get all suppliers
    cur.execute(
        """
        SELECT supplier_id, supplier_name, phone, email, address
        FROM suppliers
        ORDER BY supplier_id
        """
    )

    suppliers = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Suppliers</title>

        <style>

            body {
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                color: #333;
            }

            .navbar {
                background-color: #1f2937;
                padding: 18px 35px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .navbar h2 {
                margin: 0;
            }

            .navbar a {
                color: white;
                text-decoration: none;
                margin-left: 25px;
            }

            .container {
                padding: 35px;
            }

            .form-box {
                background: white;
                padding: 25px;
                border-radius: 10px;
                max-width: 600px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }

            label {
                display: block;
                margin-top: 15px;
                margin-bottom: 5px;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 10px;
                box-sizing: border-box;
            }

            button {
                margin-top: 20px;
                padding: 12px 20px;
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }

            table {
                margin-top: 30px;
                width: 100%;
                border-collapse: collapse;
                background: white;
            }

            th, td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: left;
            }

            th {
                background-color: #1f2937;
                color: white;
            }

        </style>

    </head>

    <body>

        <div class="navbar">
    <h2>Inventory Management System</h2>

    <div>
        <a href="/dashboard">Dashboard</a>
        <a href="/products">Products</a>
        <a href="/categories">Categories</a>
        <a href="/suppliers">Suppliers</a>
        <a href="/stock-transactions">Stock Transactions</a>
        <a href="/reports">Reports</a>
    </div>
</div>

        </div>

        <div class="container">

            <h1>Suppliers</h1>

            <div class="form-box">

                <h2>Add New Supplier</h2>

                <form method="POST">

                    <label>Supplier Name</label>

                    <input
                        type="text"
                        name="supplier_name"
                        required
                    >

                    <label>Phone</label>

                    <input
                        type="text"
                        name="phone"
                        required
                    >

                    <label>Email</label>

                    <input
                        type="email"
                        name="email"
                        required
                    >

                    <label>Address</label>

                    <input
                        type="text"
                        name="address"
                        required
                    >

                    <button type="submit">
                        Add Supplier
                    </button>

                </form>

            </div>

            <h2>Supplier List</h2>

            <table>

                
    """

    for supplier in suppliers:
        html += f"""
            <tr>
                <td>{supplier[0]}</td>
                <td>{supplier[1]}</td>
                <td>{supplier[2]}</td>
                <td>{supplier[3]}</td>
                <td>{supplier[4]}</td>
                <td>
                    <a href="/delete-supplier/{supplier[0]}"
                       onclick="return confirm('Are you sure you want to delete this supplier?');">
                        Delete
                    </a>
                </td>
            </tr>
        """
    html += """
            </table>

        </div>

    </body>

    </html>
    """

    return html
@app.route("/delete-supplier/<int:supplier_id>")
def delete_supplier(supplier_id):

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if any product is using this supplier
    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE supplier_id = %s
    """, (supplier_id,))

    count = cur.fetchone()[0]

    if count > 0:
        cur.close()
        conn.close()
        flash("Cannot delete supplier because products are using it.")
        return redirect("/suppliers")

    cur.execute("""
        DELETE FROM suppliers
        WHERE supplier_id = %s
    """, (supplier_id,))

    conn.commit()

    cur.close()
    conn.close()

    flash("Supplier deleted successfully!")

    return redirect("/suppliers")




@app.route("/view-product/<int:product_id>")
def view_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            c.category_name,
            s.supplier_name,
            p.price,
            p.quantity,
            p.reorder_level
        FROM products p
        JOIN categories c
            ON p.category_id = c.category_id
        JOIN suppliers s
            ON p.supplier_id = s.supplier_id
        WHERE p.product_id = %s
    """, (product_id,))

    product = cur.fetchone()

    cur.close()
    conn.close()

    if not product:
        return "Product not found."

    return f"""
    <h1>Product Details</h1>

    <p><strong>Product ID:</strong> {product[0]}</p>

    <p><strong>Product Name:</strong> {product[1]}</p>

    <p><strong>Category:</strong> {product[2]}</p>

    <p><strong>Supplier:</strong> {product[3]}</p>

    <p><strong>Price:</strong> ₹{product[4]}</p>

    <p><strong>Quantity:</strong> {product[5]}</p>

    <p><strong>Reorder Level:</strong> {product[6]}</p>

    <br>

    <a href="/products">Back to Products</a>
    """


@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        product_name = request.form["product_name"]
        category_id = request.form["category_id"]
        supplier_id = request.form["supplier_id"]
        price = request.form["price"]
        quantity = request.form["quantity"]
        reorder_level = request.form["reorder_level"]

        cur.execute("""
            UPDATE products
            SET product_name = %s,
                category_id = %s,
                supplier_id = %s,
                price = %s,
                quantity = %s,
                reorder_level = %s
            WHERE product_id = %s
        """, (
            product_name,
            category_id,
            supplier_id,
            price,
            quantity,
            reorder_level,
            product_id
        ))

        conn.commit()
        flash("Product updated successfully!")

        cur.close()
        conn.close()

        return redirect("/products")

    # Get product details
    cur.execute("""
        SELECT *
        FROM products
        WHERE product_id = %s
    """, (product_id,))

    product = cur.fetchone()

    # Get categories
    cur.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cur.fetchall()

    # Get suppliers
    cur.execute("""
        SELECT supplier_id, supplier_name
        FROM suppliers
        ORDER BY supplier_name
    """)

    suppliers = cur.fetchall()

    cur.close()
    conn.close()

    return f"""
    <h1>Edit Product</h1>

    <form method="POST">

        Product Name:
        <input type="text"
               name="product_name"
               value="{product[1]}"
               required>
        <br><br>

        Category:
        <select name="category_id" required>
            <option value="">Select Category</option>
            {''.join(
                f'<option value="{category[0]}" '
                f'{"selected" if category[0] == product[2] else ""}>'
                f'{category[1]}</option>'
                for category in categories
            )}
        </select>
        <br><br>

        Supplier:
        <select name="supplier_id" required>
            <option value="">Select Supplier</option>
            {''.join(
                f'<option value="{supplier[0]}" '
                f'{"selected" if supplier[0] == product[3] else ""}>'
                f'{supplier[1]}</option>'
                for supplier in suppliers
            )}
        </select>
        <br><br>

        Price:
        <input type="number"
               step="0.01"
               name="price"
               value="{product[4]}"
               required>
        <br><br>

        Quantity:
        <input type="number"
               name="quantity"
               value="{product[5]}"
               min="0"
               required>
        <br><br>

        Reorder Level:
        <input type="number"
               name="reorder_level"
               value="{product[6]}"
               min="0"
               required>
        <br><br>

        <button type="submit">Update Product</button>

    </form>
    """


@app.route("/delete-product/<int:product_id>")
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Check whether product is used in stock transactions
    cur.execute("""
        SELECT COUNT(*)
        FROM stock_transactions
        WHERE product_id = %s
    """, (product_id,))

    count = cur.fetchone()[0]

    # Do not delete products that have transaction history
    if count > 0:
        cur.close()
        conn.close()
        return """
        <h2>Cannot Delete Product</h2>
        <p>This product has stock transaction history.</p>
        <a href="/products">Back to Products</a>
        """

    # Delete product
    cur.execute("""
        DELETE FROM products
        WHERE product_id = %s
    """, (product_id,))

    conn.commit()

    cur.close()
    conn.close()


    flash("Product deleted successfully!")
    return redirect("/products")

@app.route("/stock-transactions", methods=["GET", "POST"])
def stock_transactions():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        product_id = request.form["product_id"]
        transaction_type = request.form["transaction_type"]
        quantity = int(request.form["quantity"])

        if quantity <= 0:
            flash("Quantity must be greater than 0!")
            return redirect("/stock-transactions")
        # Get current stock
        cur.execute(
            "SELECT quantity FROM products WHERE product_id = %s",
            (product_id,)
        )

        current_stock = cur.fetchone()[0]

        if transaction_type == "OUT" and quantity > current_stock:
            cur.close()
            conn.close()
            flash("Not enough stock available!")
            return redirect("/stock-transactions")
        # Update stock
        if transaction_type == "IN":
            new_stock = current_stock + quantity
        else:
            new_stock = current_stock - quantity

        cur.execute(
            "UPDATE products SET quantity = %s WHERE product_id = %s",
            (new_stock, product_id)
        )

        # Save transaction
        cur.execute("""
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity)
            VALUES (%s, %s, %s)
        """, (
            product_id,
            transaction_type,
            quantity
        ))

        conn.commit()
        flash("Stock transaction recorded successfully!")

    # Product dropdown
    cur.execute("""
        SELECT product_id, product_name
        FROM products
        ORDER BY product_name
    """)

    products = cur.fetchall()

    # Transaction history
    cur.execute("""
        SELECT
            st.transaction_id,
            p.product_name,
            st.transaction_type,
            st.quantity,
            st.transaction_date
        FROM stock_transactions st
        JOIN products p
            ON st.product_id = p.product_id
        ORDER BY st.transaction_date DESC
    """)

    transactions = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Stock Transactions</title>

        <style>

            body{
                font-family:Arial;
                background:#f4f6f8;
                margin:0;
            }

            .navbar{
                background:#1f2937;
                color:white;
                padding:18px 35px;
            }

            .navbar a{
                color:white;
                text-decoration:none;
                margin-right:20px;
            }

            .container{
                padding:35px;
            }

            .card{
                background:white;
                padding:25px;
                border-radius:10px;
                max-width:600px;
                margin-bottom:30px;
            }

            input,select{
                width:100%;
                padding:10px;
                margin:8px 0 16px;
                box-sizing:border-box;
            }

            button{
                background:#1f2937;
                color:white;
                border:none;
                padding:12px 20px;
                border-radius:6px;
                cursor:pointer;
            }

            table{
                width:100%;
                border-collapse:collapse;
                background:white;
            }

            th,td{
                border:1px solid #ddd;
                padding:12px;
                text-align:left;
            }

            th{
                background:#1f2937;
                color:white;
            }

            .in{
                color:green;
                font-weight:bold;
            }

            .out{
                color:red;
                font-weight:bold;
            }

        </style>

    </head>

    <body>

        <div class="navbar">
    <h2>Inventory Management System</h2>

    <div>
        <a href="/dashboard">Dashboard</a>
        <a href="/products">Products</a>
        <a href="/categories">Categories</a>
        <a href="/suppliers">Suppliers</a>
        <a href="/stock-transactions">Stock Transactions</a>
        <a href="/reports">Reports</a>
    </div>
</div>

        <div class="container">

            <div class="card">

                <h2>Record Stock Transaction</h2>

                <form method="POST">

                    <label>Product</label>

                    <select name="product_id" required>

                        <option value="">Select Product</option>
    """

    for product in products:

        html += f"""
                        <option value="{product[0]}">
                            {product[1]}
                        </option>
        """

    html += """

                    </select>

                    <label>Transaction Type</label>

                    <select name="transaction_type" required>

                        <option value="IN">
                            Stock IN
                        </option>

                        <option value="OUT">
                            Stock OUT
                        </option>

                    </select>

                    <label>Quantity</label>

                    <input
                        type="number"
                        name="quantity"
                        min="1"
                        required
                    >

                    <button type="submit">
                        Record Transaction
                    </button>

                </form>

            </div>

            <h2>Transaction History</h2>

            <table>

                <tr>
                    <th>ID</th>
                    <th>Product</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Date</th>
                </tr>
    """

    for t in transactions:

        colour = "in" if t[2] == "IN" else "out"

        html += f"""
                <tr>
                    <td>{t[0]}</td>
                    <td>{t[1]}</td>
                    <td class="{colour}">{t[2]}</td>
                    <td>{t[3]}</td>
                    <td>{t[4]}</td>
                </tr>
        """

    html += """

            </table>

        </div>

    </body>

    </html>
    """

    return html
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Total Products
    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    # 2. Total Stock
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM products
    """)
    total_stock = cur.fetchone()[0]

    # 3. Low Stock Products
    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity <= reorder_level
    """)
    low_stock = cur.fetchone()[0]

    # 4. Total Stock IN
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM stock_transactions
        WHERE transaction_type = 'IN'
    """)
    total_stock_in = cur.fetchone()[0]

    # 5. Total Stock OUT
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM stock_transactions
        WHERE transaction_type = 'OUT'
    """)
    total_stock_out = cur.fetchone()[0]

    # 6. Total Inventory Value
    cur.execute("""
        SELECT COALESCE(SUM(price * quantity), 0)
        FROM products
    """)
    total_inventory_value = cur.fetchone()[0]

    # 7. Low Stock Product Details
    cur.execute("""
        SELECT
            p.product_name,
            c.category_name,
            p.quantity,
            p.reorder_level
        FROM products p
        JOIN categories c
            ON p.category_id = c.category_id
        WHERE p.quantity <= p.reorder_level
        ORDER BY p.quantity ASC
    """)

    low_stock_products = cur.fetchall()

    cur.close()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>

    <head>

        <title>Inventory Dashboard</title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                background-color: #f4f6f8;
                color: #333;
            }}

            .navbar {{
                background-color: #1f2937;
                padding: 18px 35px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .navbar h2 {{
                margin: 0;
            }}

            .navbar a {{
                color: white;
                text-decoration: none;
                margin-left: 22px;
            }}

            .navbar a:hover {{
                text-decoration: underline;
            }}

            .container {{
                padding: 35px;
            }}

            .container h1 {{
                margin-bottom: 30px;
            }}

            .cards {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 35px;
            }}

            .card {{
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }}

            .card h3 {{
                margin: 0 0 15px;
                font-size: 16px;
                color: #666;
            }}

            .card p {{
                margin: 0;
                font-size: 30px;
                font-weight: bold;
            }}

            .products {{
                border-left: 5px solid #8e44ad;
            }}

            .quantity {{
                border-left: 5px solid #f39c12;
            }}

            .low-stock {{
                border-left: 5px solid #e74c3c;
            }}

            .stock-in {{
                border-left: 5px solid #27ae60;
            }}

            .stock-out {{
                border-left: 5px solid #3498db;
            }}

            .value {{
                border-left: 5px solid #16a085;
            }}

            .section {{
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }}

            .section h2 {{
                margin-top: 0;
                margin-bottom: 20px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th, td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}

            th {{
                background-color: #f1f3f5;
            }}

            .warning {{
                color: #e74c3c;
                font-weight: bold;
            }}

            .normal {{
                color: #333;
            }}

            @media (max-width: 900px) {{
                .cards {{
                    grid-template-columns: repeat(2, 1fr);
                }}

                .navbar {{
                    flex-direction: column;
                    gap: 15px;
                }}
            }}

        </style>

    </head>

    <body>

        <div class="navbar">

            <h2>Inventory Management System</h2>

            <div>
                <a href="/dashboard">Dashboard</a>
                <a href="/products">Products</a>
                <a href="/categories">Categories</a>
                <a href="/suppliers">Suppliers</a>
                <a href="/stock-transactions">Stock Transactions</a>
                <a href="/reports">Reports</a>
            </div>

        </div>


        <div class="container">

            <h1>Inventory Dashboard</h1>


            <div class="cards">

                <div class="card products">
                    <h3>Total Products</h3>
                    <p>{total_products}</p>
                </div>


                <div class="card quantity">
                    <h3>Total Stock</h3>
                    <p>{total_stock}</p>
                </div>


                <div class="card low-stock">
                    <h3>Low Stock</h3>
                    <p>{low_stock}</p>
                </div>


                <div class="card stock-in">
                    <h3>Stock IN</h3>
                    <p>{total_stock_in}</p>
                </div>


                <div class="card stock-out">
                    <h3>Stock OUT</h3>
                    <p>{total_stock_out}</p>
                </div>


                <div class="card value">
                    <h3>Inventory Value</h3>
                    <p>₹{total_inventory_value}</p>
                </div>

            </div>


            <div class="section">

                <h2>Low Stock Products</h2>

                <table>

                    <tr>
                        <th>Product</th>
                        <th>Category</th>
                        <th>Current Stock</th>
                        <th>Reorder Level</th>
                        <th>Status</th>
                    </tr>

                    {
                        ''.join(
                            f'''
                            <tr>
                                <td>{p[0]}</td>
                                <td>{p[1]}</td>
                                <td class="warning">{p[2]}</td>
                                <td>{p[3]}</td>
                                <td class="warning">Low Stock</td>
                            </tr>
                            '''
                            for p in low_stock_products
                        )
                        if low_stock_products
                        else '''
                            <tr>
                                <td colspan="5">
                                    No low stock products 🎉
                                </td>
                            </tr>
                        '''
                    }

                </table>

            </div>

        </div>

    </body>

    </html>
    """

@app.route("/reports")
def reports():

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Low Stock Report
    cur.execute("""
        SELECT
            p.product_name,
            c.category_name,
            p.quantity,
            p.reorder_level
        FROM products p
        JOIN categories c
            ON p.category_id = c.category_id
        WHERE p.quantity <= p.reorder_level
        ORDER BY p.quantity
    """)

    low_stock = cur.fetchall()

    # 2. Inventory Value Report
    cur.execute("""
        SELECT
            p.product_name,
            c.category_name,
            p.price,
            p.quantity,
            (p.price * p.quantity) AS inventory_value
        FROM products p
        JOIN categories c
            ON p.category_id = c.category_id
        ORDER BY inventory_value DESC
    """)

    inventory_value = cur.fetchall()

    # 3. Stock IN vs OUT Summary
    cur.execute("""
        SELECT
            transaction_type,
            SUM(quantity) AS total_quantity
        FROM stock_transactions
        GROUP BY transaction_type
        ORDER BY transaction_type
    """)

    stock_summary = cur.fetchall()

    # 4. Products by Category
    cur.execute("""
        SELECT
            c.category_name,
            COUNT(p.product_id) AS total_products
        FROM categories c
        LEFT JOIN products p
            ON c.category_id = p.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY total_products DESC
    """)

    category_summary = cur.fetchall()

    # 5. Summary Statistics
    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity <= reorder_level
    """)
    low_stock_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM stock_transactions
        WHERE transaction_type = 'IN'
    """)
    total_stock_in = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM stock_transactions
        WHERE transaction_type = 'OUT'
    """)
    total_stock_out = cur.fetchone()[0]

    cur.close()
    conn.close()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reports</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js">
        </script>
        <style>
            body {{
                font-family: Arial;
                background: #f4f6f8;
                margin: 0;
            }}

            .navbar {{
                background: #1f2937;
                padding: 18px 35px;
            }}

            .navbar a {{
                color: white;
                text-decoration: none;
                margin-right: 20px;
            }}

            .container {{
                padding: 35px;
            }}
                        .page-header {{
                background: white;
                padding: 25px 30px;
                border-radius: 12px;
                margin-bottom: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}

            .page-header h1 {{
                margin: 0 0 8px 0;
                font-size: 30px;
                color: #1f2937;
            }}

            .page-header p {{
                margin: 0;
                color: #6b7280;
                font-size: 15px;
            }}

            .summary-cards {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 25px;
            }}

            .summary-card {{
                background: white;
                padding: 22px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}

            .summary-card h3 {{
                margin: 0 0 10px 0;
                color: #6b7280;
                font-size: 14px;
                font-weight: normal;
            }}

            .summary-card .number {{
                font-size: 28px;
                font-weight: bold;
                color: #1f2937;
            }}
            .summary-card {{
    border-top: 4px solid #3498db;
}}

.summary-card:nth-child(2) {{
    border-top-color: #e74c3c;
}}

.summary-card:nth-child(3) {{
    border-top-color: #27ae60;
}}

.summary-card:nth-child(4) {{
    border-top-color: #f39c12;
}}

            @media (max-width: 900px) {{
                .summary-cards {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            


                        .report {{
    background: white;
    padding: 25px 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #eef0f3;
}}

            .report h2 {{
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 21px;
                color: #1f2937;
            }}
            .report canvas {{
    background: #ffffff;
    padding: 10px;
}}

            table {{
                width: 100%;
                border-collapse: collapse;
                overflow: hidden;
                border-radius: 8px;
            }}

            th {{
                background: #1f2937;
                color: white;
                padding: 13px;
                text-align: left;
                font-size: 14px;
            }}

            td {{
                padding: 13px;
                border-bottom: 1px solid #e5e7eb;
                text-align: left;
                font-size: 14px;
            }}

            tr:hover td {{
                background: #f9fafb;
            }}

            .warning {{
    color: #dc2626;
    font-weight: bold;
    background: #fee2e2;
    padding: 6px 10px;
    border-radius: 6px;
    display: inline-block;
}}
.stock-type {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}}

.stock-type.in {{
    color: #15803d;
    background: #dcfce7;
}}

.stock-type.out {{
    color: #dc2626;
    background: #fee2e2;
}}
        </style>
    </head>

    <body>

        <div class="navbar">
            <a href="/dashboard">Dashboard</a>
            <a href="/products">Products</a>
            <a href="/categories">Categories</a>
            <a href="/suppliers">Suppliers</a>
            <a href="/stock-transactions">Transactions</a>
            <a href="/reports">Reports</a>
        </div>

        <div class="container">

    <div class="page-header">
        <div>
            <h1>Inventory Reports</h1>
            <p>Overview of your inventory, stock movement and product distribution</p>
        </div>
    </div>
    
    <div class="summary-cards">

    <div class="summary-card">
        <h3>Total Products</h3>
        <div class="number">{total_products}</div>
    </div>

    <div class="summary-card">
        <h3>Low Stock Items</h3>
        <div class="number">{low_stock_count}</div>
    </div>

    <div class="summary-card">
        <h3>Total Stock IN</h3>
        <div class="number">{total_stock_in}</div>
    </div>

    <div class="summary-card">
        <h3>Total Stock OUT</h3>
        <div class="number">{total_stock_out}</div>
    </div>

</div>
            <div class="report">

                <h2>Low Stock Report</h2>
                <p style="color: #6b7280; margin-top: -10px; margin-bottom: 20px;">
    Products that have reached or fallen below their reorder level
</p>

                <table>

                    <tr>
                        <th>Product</th>
                        <th>Category</th>
                        <th>Current Stock</th>
                       <th>Reorder Level</th>
                       <th>Status</th>
                    </tr>

                    {''.join(
                        f'''
                        <tr>
                            <td>{item[0]}</td>
                            <td>{item[1]}</td>
                            <td class="warning">{item[2]}</td>
                            <td>{item[3]}</td>
<td>
    <span class="warning">
        {'Critical' if item[2] <= 2 else 'Low'}
    </span>
</td>
                        </tr>
                        '''
                        for item in low_stock
                    )}

                </table>

            </div>


           <div class="report">

    <h2>Total Inventory Value</h2>
<p style="color:#666; margin-top:-10px;">
    Estimated value of current stock based on product price and quantity
</p>

    <div style="max-width: 800px; margin: 20px auto;">
        <canvas id="inventoryValueChart"></canvas>
    </div>

    <table>
                    <tr>
                        <th>Product</th>
                        <th>Category</th>
                        <th>Price (₹)</th>
                        <th>Quantity</th>
                        <th>Inventory Value (₹)</th>
                    </tr>

                    {''.join(
                        f'''
                        <tr>
                            <td>{item[0]}</td>
                            <td>{item[1]}</td>
                            <td>₹{item[2]}</td>
                            <td>{item[3]}</td>
                            <td>₹{item[4]:,.2f}</td>
                        </tr>
                        '''
                        for item in inventory_value
                    )}

                </table>

            </div>


           <div class="report">

    <h2>Stock Movement</h2>
<p style="color:#666; margin-top:-10px;">
    Comparison of total stock received and issued
</p>

    <div style="max-width: 700px; margin: 20px auto;">
        <canvas id="stockChart"></canvas>
    </div>

    <table>

                    <tr>
                        <th>Transaction Type</th>
                        <th>Total Quantity</th>
                    </tr>

                    {''.join(
                        f'''
                        <tr>
                           <td>
    <span class="stock-type {item[0].lower()}">{item[0]}</span>
</td>
                            <td>{item[1]}</td>
                        </tr>
                        '''
                        for item in stock_summary
                    )}

                </table>

            </div>


            <div class="report">

   <h2>Product Distribution by Category</h2>
<p style="color:#666; margin-top:-10px;">
    Number of products available in each category
</p>
    <div style="max-width: 550px; margin: 20px auto;">
        <canvas id="categoryChart"></canvas>
    </div>

    <table>

                    <tr>
                        <th>Category</th>
                        <th>Total Products</th>
                    </tr>

                    {''.join(
                        f'''
                        <tr>
                            <td>{item[0]}</td>
                            <td>{item[1]}</td>
                        </tr>
                        '''
                        for item in category_summary
                    )}

                </table>

            </div>

        </div>
        <script>

    const stockLabels = [
        {','.join(f'"{item[0]}"' for item in stock_summary)}
    ];

    const stockValues = [
        {','.join(str(item[1]) for item in stock_summary)}
    ];

    new Chart(document.getElementById("stockChart"), {{

        type: "bar",

        data: {{
            labels: stockLabels,

            datasets: [{{
                label: "Quantity",
                data: stockValues
            }}]
        }},

        options: {{
            responsive: true,

            scales: {{
                y: {{
                    beginAtZero: true
                }}
            }}
        }}

    }});

</script>
<script>

    const categoryLabels = [
        {','.join(f'"{item[0]}"' for item in category_summary)}
    ];

    const categoryValues = [
        {','.join(str(item[1]) for item in category_summary)}
    ];

    new Chart(document.getElementById("categoryChart"), {{

        type: "doughnut",

        data: {{
            labels: categoryLabels,

            datasets: [{{
                label: "Products",
                data: categoryValues,
                backgroundColor: [
                    "#3498db",
                    "#27ae60",
                    "#f39c12",
                    "#e74c3c",
                    "#8e44ad",
                    "#16a085",
                    "#34495e",
                    "#e67e22",
                    "#2ecc71",
                    "#9b59b6"
                ],
                borderWidth: 1
            }}]
        }},

        options: {{
            responsive: true,

            plugins: {{
                legend: {{
                    position: "bottom"
                }}
            }}
        }}

    }});

</script>

<script>

    const inventoryLabels = [
        {','.join(f'"{item[0]}"' for item in inventory_value)}
    ];

    const inventoryValues = [
        {','.join(str(item[4]) for item in inventory_value)}
    ];

    new Chart(document.getElementById("inventoryValueChart"), {{

        type: "bar",

        data: {{
            labels: inventoryLabels,

            datasets: [{{
                label: "Inventory Value",
                data: inventoryValues
            }}]
        }},

        options: {{
            responsive: true,

            scales: {{
                y: {{
                    beginAtZero: true
                }}
            }}
        }}

    }});

</script>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)