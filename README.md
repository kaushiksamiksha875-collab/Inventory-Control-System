# Inventory Control System

A web-based Inventory Control System developed using Flask and PostgreSQL.

## Project Overview

The Inventory Control System helps manage products, categories, suppliers, and stock transactions in a centralized database.

## Features

- User Login and Logout
- Dashboard with inventory statistics
- Product Management
  - Add products
  - View products
  - Edit products
  - Delete products
  - Search products
  - Filter products by category
  - Low-stock identification
- Category Management
- Supplier Management
- Stock IN and Stock OUT
- Stock quantity validation
- Transaction history
- Inventory reports
- Inventory value calculation
- Stock movement reports
- Product distribution by category
- Charts and visual reports

## Technologies Used

- Python
- Flask
- PostgreSQL
- HTML
- CSS
- Python-dotenv
- Gunicorn

## Database

The system uses PostgreSQL for storing:

- Users
- Categories
- Suppliers
- Products
- Stock Transactions

## Running the Project Locally

1. Clone the repository.

2. Create and activate a Python virtual environment.

3. Install the required packages:

```bash
pip install -r requirements.txt