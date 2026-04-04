from extensions import db
from datetime import datetime

class JioMartProduct(db.Model):
    __tablename__ = 'jio_mart_products'

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
    Reliance_One_Card = db.Column(db.Boolean)
    Kirana_Partner_ID = db.Column(db.String(100))
    FB_Integration_ID = db.Column(db.String(100))
    Offer_Zone_ID = db.Column(db.String(100))
    Payment_Gateway = db.Column(db.String(100))
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
            "reliance_one_card": self.Reliance_One_Card,
            "kirana_partner_id": self.Kirana_Partner_ID,
            "fb_integration_id": self.FB_Integration_ID,
            "offer_zone_id": self.Offer_Zone_ID,
            "payment_gateway": self.Payment_Gateway,
            "created_at": created_str
        }