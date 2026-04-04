from extensions import db
from datetime import datetime

class ZeptoProduct(db.Model):
    __tablename__ = 'zepto_products'

    id = db.Column(db.Integer, primary_key=True)
    Product_ID = db.Column(db.String(100), unique=True)
    SKU = db.Column(db.String(100))
    Name = db.Column(db.Text)
    Brand = db.Column(db.String(255))
    Base_Price = db.Column(db.String(100))
    Quantity_In_Stock = db.Column(db.Integer)
    User_ID = db.Column(db.Integer)
    Email = db.Column(db.String(255))
    Seller_Name = db.Column(db.String(255))
    User_Address = db.Column(db.Text)
    Order_ID = db.Column(db.String(100))
    Order_Date = db.Column(db.DateTime)
    Status = db.Column(db.String(100))
    Opening_Hours = db.Column(db.String(100))
    Established_Year = db.Column(db.Integer)
    Rating = db.Column(db.String(50))
    Website = db.Column(db.String(255))
    URL = db.Column(db.Text)
    Review_Count = db.Column(db.Integer)
    Average_Review_Star_Ratings = db.Column(db.String(50))
    Review_Date = db.Column(db.DateTime)
    Product_Subcategory = db.Column(db.String(255))
    Available_Coupon = db.Column(db.Text)
    stock_quantity = db.Column(db.Integer)
    img_url = db.Column(db.Text)
    weight_or_volume = db.Column(db.String(100))
    quantity = db.Column(db.String(100))
    delivery_fee = db.Column(db.String(100))
    delivery_slot = db.Column(db.String(100))
    tax = db.Column(db.String(100))
    discount = db.Column(db.String(100))
    payment_method = db.Column(db.String(100))
    transaction_id = db.Column(db.String(100))
    payment_status = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime)
    refund_amount = db.Column(db.String(100))
    reason = db.Column(db.Text)
    refund_status = db.Column(db.String(100))
    delivery_time = db.Column(db.String(100))
    max_discount = db.Column(db.String(100))
    expiry_date = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        created_str = self.created_at
        if hasattr(self.created_at, 'isoformat'):
            created_str = self.created_at.isoformat()
        
        review_date_str = None
        if self.Review_Date and hasattr(self.Review_Date, 'isoformat'):
            review_date_str = self.Review_Date.isoformat()
        
        order_date_str = None
        if self.Order_Date and hasattr(self.Order_Date, 'isoformat'):
            order_date_str = self.Order_Date.isoformat()
        
        paid_at_str = None
        if self.paid_at and hasattr(self.paid_at, 'isoformat'):
            paid_at_str = self.paid_at.isoformat()
        
        expiry_date_str = None
        if self.expiry_date and hasattr(self.expiry_date, 'isoformat'):
            expiry_date_str = self.expiry_date.isoformat()
        
        return {
            "id": self.id,
            "product_id": self.Product_ID,
            "sku": self.SKU,
            "name": self.Name,
            "brand": self.Brand,
            "base_price": self.Base_Price,
            "quantity_in_stock": self.Quantity_In_Stock,
            "user_id": self.User_ID,
            "email": self.Email,
            "seller_name": self.Seller_Name,
            "user_address": self.User_Address,
            "order_id": self.Order_ID,
            "order_date": order_date_str,
            "status": self.Status,
            "opening_hours": self.Opening_Hours,
            "established_year": self.Established_Year,
            "rating": self.Rating,
            "website": self.Website,
            "url": self.URL,
            "review_count": self.Review_Count,
            "average_review_star_ratings": self.Average_Review_Star_Ratings,
            "review_date": review_date_str,
            "product_subcategory": self.Product_Subcategory,
            "available_coupon": self.Available_Coupon,
            "stock_quantity": self.stock_quantity,
            "img_url": self.img_url,
            "weight_or_volume": self.weight_or_volume,
            "quantity": self.quantity,
            "delivery_fee": self.delivery_fee,
            "delivery_slot": self.delivery_slot,
            "tax": self.tax,
            "discount": self.discount,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "payment_status": self.payment_status,
            "paid_at": paid_at_str,
            "refund_amount": self.refund_amount,
            "reason": self.reason,
            "refund_status": self.refund_status,
            "delivery_time": self.delivery_time,
            "max_discount": self.max_discount,
            "expiry_date": expiry_date_str,
            "usage_limit": self.usage_limit,
            "description": self.description,
            "created_at": created_str
        }