PRAGMA foreign_keys = ON;
CREATE TABLE Categories(category_id INT PRIMARY KEY, category_name VARCHAR(50));
CREATE TABLE Suppliers(supplier_id INT PRIMARY KEY, supplier_name VARCHAR(100), phone VARCHAR(15));
CREATE TABLE Products(
  product_id INT PRIMARY KEY, product_name VARCHAR(100), category_id INT, supplier_id INT,
  price DECIMAL(10,2), stock_quantity INT,
  FOREIGN KEY(category_id) REFERENCES Categories(category_id),
  FOREIGN KEY(supplier_id) REFERENCES Suppliers(supplier_id)
);
CREATE TABLE Customers(customer_id INT PRIMARY KEY, customer_name VARCHAR(100), email VARCHAR(100), phone VARCHAR(15));
CREATE TABLE Orders(
  order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL(10,2),
  FOREIGN KEY(customer_id) REFERENCES Customers(customer_id)
);
CREATE TABLE Order_Items(
  item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, subtotal DECIMAL(10,2),
  FOREIGN KEY(order_id) REFERENCES Orders(order_id),
  FOREIGN KEY(product_id) REFERENCES Products(product_id)
);

INSERT INTO Categories VALUES (1,'Electronics'),(2,'Clothing'),(3,'Accessories');
INSERT INTO Suppliers VALUES (1,'ABC Suppliers','9876543210'),(2,'XYZ Traders','9876501234');
INSERT INTO Products VALUES
(101,'Headphones',1,1,1500.00,20),(102,'T-Shirt',2,2,500.00,50),
(103,'Smart Watch',1,1,3000.00,10),(104,'Handbag',3,2,1200.00,15);
INSERT INTO Customers VALUES
(1,'Arun','arun@gmail.com','9876543211'),(2,'Priya','priya@gmail.com','9876543212');
INSERT INTO Orders VALUES (1001,1,'2026-10-20',3000.00),(1002,2,'2026-10-21',1000.00);
INSERT INTO Order_Items VALUES (1,1001,101,2,3000.00),(2,1002,102,2,1000.00);
