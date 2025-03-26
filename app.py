from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

app = Flask(__name__)
url = os.getenv('DATABASE_URL')
connection = psycopg2.connect(url)

@app.get('/')
def home():
     return render_template("home.html")

@app.get('/list')
def list_data():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Manufacturer;")
        manufacturers = cursor.fetchall()
        
        cursor.execute("SELECT * FROM Car;")
        cars = cursor.fetchall()

        cursor.execute("SELECT * FROM BodyType;")
        bodytypes = cursor.fetchall()

        cursor.execute("SELECT * FROM Customer;")
        customers = cursor.fetchall()

        cursor.execute("SELECT * FROM Orders;")
        orders = cursor.fetchall()

    return render_template("list.html", manufacturers=manufacturers, cars=cars, bodytypes=bodytypes, customers=customers, orders=orders)

@app.route('/add_manufacturer', methods=['GET', 'POST'])
def add_manufacturer():
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Manufacturer (make, model, year, colour) VALUES (%s, %s, %s, %s);",
                    (request.form['make'], request.form['model'], request.form['year'], request.form['colour'])
                )
                connection.commit()

            return redirect(url_for('list_data'))  # Redirect to the list data page after adding the manufacturer

        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"
        
    return render_template("add_manufacturer.html")  # Render the add manufacturer form page

@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Car (mileage, price, transmission, mID) VALUES (%s, %s, %s, %s);",
                    (request.form['mileage'], request.form['price'], request.form['transmission'], request.form['manufacturer_id'])
                )
                connection.commit()

            return redirect(url_for('list_data'))  # Redirect to the list data page after adding the car

        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"
        
        # Query manufacturers for the dropdown and table
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Manufacturer;")
        manufacturers = cursor.fetchall()
            
    return render_template("add_car.html", manufacturers=manufacturers)  # Render the add car form page

@app.route('/add_bodytype', methods=['GET', 'POST'])
def add_bodytype():
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO BodyType (b_type, num_doors, cID) VALUES (%s, %s, %s);",
                    (request.form['b_type'], request.form['num_doors'], request.form['car_id'])
                )
                connection.commit()

            return redirect(url_for('list_data'))  # Redirect to the list data page after adding the body type

        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"
        
    
    # Query cars for the dropdown and table
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Car;")
        cars = cursor.fetchall()
        
    return render_template("add_bodytype.html", cars=cars)  # Render the add body type form page

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Customer (name, phone_num) VALUES (%s, %s);",
                    (request.form['name'], request.form['phone_num'])
                )
                connection.commit()

            return redirect(url_for('list_data'))  # Redirect to the list data page after adding the customer

        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"
        
    return render_template("add_customer.html") 

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        try:
            # Get the customer and car IDs, and order date from the form
            date = request.form['date']
            car_id = request.form['car_id']
            customer_id = request.form['customer_id']
            
            with connection.cursor() as cursor:
                # Insert the new order into the Orders table
                cursor.execute(
                    "INSERT INTO Orders (date, cID, customerID) VALUES (%s, %s, %s) RETURNING id;",
                    (date, car_id, customer_id)
                )
                order_id = cursor.fetchone()[0]  # Get the ID of the newly inserted order
                connection.commit()

                # Update the corresponding customer to set their 'oid' field
                cursor.execute(
                    "UPDATE Customer SET oid = %s WHERE id = %s;",
                    (order_id, customer_id)
                )
                connection.commit()

            return redirect(url_for('list_data'))  # Redirect to the list data page after adding the order

        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"

    # Fetch all customers and cars for displaying in the dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Customer;")
        customers = cursor.fetchall()
        
        cursor.execute("SELECT * FROM Car;")
        cars = cursor.fetchall()

    return render_template('add_order.html', customers=customers, cars=cars)


@app.route('/delete', methods=['GET', 'POST'])
def delete_data():
    if request.method == 'POST':
        table = request.form['table']
        record_id = request.form['id']

        # Define primary key column names for each table
        primary_keys = {
            "manufacturer": "ID",
            "car": "ID",
            "bodytype": "ID",
            "customer": "ID",
            "orders": "ID"
        }

        if table in primary_keys:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {table} WHERE {primary_keys[table]} = %s;",
                    (record_id,)
                )
                connection.commit()

        return redirect(url_for('list_data'))

    return render_template("delete.html")

@app.get('/info')
def car_info():
    try:
        with connection.cursor() as cursor:
            # Fetch vehicle details 
            cursor.execute("""
                SELECT Manufacturer.make, Manufacturer.model, Manufacturer.year, Manufacturer.colour, 
                       Car.mileage, Car.price 
                FROM Car
                JOIN Manufacturer ON Car.mID = Manufacturer.ID;
            """)
            car_details = cursor.fetchall()

            # Fetch customer orders 
            cursor.execute("""
                SELECT 
                    Customer.id AS customer_id,
                    Customer.name,
                    Customer.phone_num,
                    Orders.id AS order_id,
                    Manufacturer.make,
                    Manufacturer.model,
                    Manufacturer.year,
                    Car.price,
                    Orders.date AS date_ordered
                FROM Orders
                JOIN Customer ON Orders.customerID = Customer.id
                JOIN Car ON Orders.cid = Car.id
                JOIN Manufacturer ON Car.mID = Manufacturer.ID
                ORDER BY Orders.id;
            """)
            order_details = cursor.fetchall()

        return render_template("info.html", car_details=car_details, order_details=order_details)
    
    except psycopg2.Error as e:
        connection.rollback()  # Rollback transaction on failure
        return f"Database Error: {e}"



@app.route('/modify', methods=['GET', 'POST'])
def modify_data():
    if request.method == 'POST':
        table = request.form['table']
        record_id = request.form['id']
        column = request.form['column']
        new_value = request.form['new_value']

        try:
            with connection.cursor() as cursor:
                # Update the record in the chosen table
                query = f"UPDATE {table} SET {column} = %s WHERE ID = %s;"
                cursor.execute(query, (new_value, record_id))

                # If we're modifying the 'Order' table and we have a customer_id, update the customer table
                if table == 'Order':  # Assuming you're modifying the Order table
                    order_id = record_id  # The order ID we're updating
                    customer_id = new_value  # Assuming you associate the customer ID with the new order

                    # Update the customer's record with the order_id
                    customer_update_query = """
                        UPDATE Customer
                        SET order_id = %s  # If you want to store the order ID here
                        WHERE ID = %s;
                    """
                    cursor.execute(customer_update_query, (order_id, customer_id))
                
                connection.commit()
                return redirect(url_for('list_data'))
        except psycopg2.Error as e:
            connection.rollback()
            return f"Error: {e}"

    return render_template("modify.html")

@app.route('/get_entries')
def get_entries():
    table = request.args.get('table')
    if table:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table};")
                column_names = [desc[0] for desc in cursor.description]
                entries = cursor.fetchall()
                
                # Convert entries to a simple CSV-like text format
                data = ";".join(column_names) + "\n"  # Headers
                for row in entries:
                    data += ";".join(map(str, row)) + "\n"
                
                return data
        except psycopg2.Error as e:
            return f"Error: {e}"
    return "No data found"

# At the end of the file, this block will run when the script is executed
if __name__ == "__main__":
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)