import pandas as pd
from sqlmodel import Session, select
from app.models.all_models import Product, Category, Customer, Sale

class ExcelParser:
    def __init__(self, file, db: Session):
        self.file = file
        self.db = db
        self.df = pd.read_excel(file)
        self.errors = []

    def _normalize_columns(self):
        """Normalizes column names to lowercase and replaces spaces with underscores."""
        self.df.columns = [col.lower().replace(' ', '_') for col in self.df.columns]
        # TODO: Add validation for required columns

    def _get_or_create_category(self, name: str) -> Category:
        """Finds a category by name or creates it if it doesn't exist."""
        category = self.db.exec(select(Category).where(Category.name == name)).first()
        if not category:
            category = Category(name=name)
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
        return category

    def _get_or_create_customer(self, name: str, email: str) -> Customer:
        """Finds a customer by email or creates them."""
        customer = self.db.exec(select(Customer).where(Customer.email == email)).first()
        if not customer:
            customer = Customer(name=name, email=email)
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
        return customer

    def run(self):
        """Main method to parse the dataframe and populate the database."""
        self._normalize_columns()

        for index, row in self.df.iterrows():
            try:
                # TODO: Add robust error handling and data validation (e.g., with Pydantic)
                
                # 1. Category
                category_name = row.get('category', 'Uncategorized')
                category = self._get_or_create_category(category_name)

                # 2. Customer
                customer_name = row.get('customer_name', 'N/A')
                customer_email = row.get('customer_email', f'unknown_{index}@example.com')
                customer = self._get_or_create_customer(customer_name, customer_email)

                # 3. Product
                sku = row['sku']
                product = self.db.exec(select(Product).where(Product.sku == sku)).first()
                if not product:
                    product = Product(
                        sku=sku,
                        name=row['product'],
                        price=float(str(row['price']).replace('R$', '').replace(',', '.').strip()),
                        stock=int(row.get('quantity', 0)), # Assuming initial stock is quantity
                        category_id=category.id
                    )
                    self.db.add(product)
                    self.db.commit()
                    self.db.refresh(product)

                # 4. Sale
                sale = Sale(
                    product_id=product.id,
                    customer_id=customer.id,
                    quantity=int(row['quantity']),
                    price_unit=product.price,
                    total=int(row['quantity']) * product.price,
                    sale_date=pd.to_datetime(row['sale_date'], dayfirst=True)
                )
                self.db.add(sale)

            except Exception as e:
                self.errors.append(f"Error on row {index}: {e}")
        
        self.db.commit()
        # TODO: Handle and log errors properly