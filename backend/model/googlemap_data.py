from extensions import db

class GoogleMapData(db.Model):
    __tablename__ = 'google_map'

    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(512))
    number = db.Column(db.String(30))
    email = db.Column(db.String(255))
    website = db.Column(db.Text)
    address = db.Column(db.String(512))
    latitude = db.Column(db.Numeric(12, 7))
    longitude = db.Column(db.Numeric(12, 7))
    rating = db.Column(db.Numeric(4, 1))
    review = db.Column(db.Text)
    category = db.Column(db.String(50))
    working_hour = db.Column(db.String(255))
    facebook_profile = db.Column(db.Text)
    instagram_profile = db.Column(db.Text)
    linkedin_profile = db.Column(db.Text)
    twitter_profile = db.Column(db.Text)
    source_name = db.Column(db.String(50))
    g_id = db.Column(db.String(512))
    gmaps_link = db.Column(db.Text)
    
    # Organization fields
    organization_name = db.Column(db.String(255))
    organization_id = db.Column(db.String(255))
    rate_stars = db.Column(db.Integer)
    reviews_total_count = db.Column(db.Integer)
    price_policy = db.Column(db.Text)
    organization_category = db.Column(db.String(255))
    organization_address = db.Column(db.Text)

    def to_dict(self):
        return {
            "name": self.business_name,
            "address": self.address,
            "phone_number": self.number,
            "category": self.category,
            "city": self.extract_city(self.address), # Helper for city
            "area": "",
            "pincode": "",
            "website": self.website,
            "rating": float(self.rating) if self.rating else 0,
            "reviews": self.reviews_total_count
        }

    def extract_city(self, address):
        if not address: return "-"
        parts = address.split(',')
        # Simple heuristic: City is often the 2nd to last part of address
        return parts[-2].strip() if len(parts) > 2 else "-"