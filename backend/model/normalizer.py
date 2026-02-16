import re
import unicodedata

# State map for canonical names
STATE_MAP = {
    # Abbreviations
    "ap": "Andhra Pradesh", "ar": "Arunachal Pradesh", "as": "Assam", "br": "Bihar",
    "cg": "Chhattisgarh", "ga": "Goa", "gj": "Gujarat", "hr": "Haryana", "hp": "Himachal Pradesh",
    "jk": "Jammu and Kashmir", "jh": "Jharkhand", "ka": "Karnataka", "kl": "Kerala",
    "mp": "Madhya Pradesh", "mh": "Maharashtra", "mn": "Manipur", "ml": "Meghalaya",
    "mz": "Mizoram", "nl": "Nagaland", "or": "Odisha", "pb": "Punjab", "rj": "Rajasthan",
    "sk": "Sikkim", "tn": "Tamil Nadu", "tg": "Telangana", "tr": "Tripura", "uttaranchal": "Uttarakhand",
    "uk": "Uttarakhand", "up": "Uttar Pradesh", "wb": "West Bengal", "dl": "Delhi",
    # Full names (no space for lookup)
    "andhrapradesh": "Andhra Pradesh",
    "aandhraapradesh": "Andhra Pradesh",
    "andhrapradhesh": "Andhra Pradesh",
    "arunachalpradesh": "Arunachal Pradesh",
    "himachalpradesh": "Himachal Pradesh",
    "jammuandkashmir": "Jammu and Kashmir",
    "madhyapradesh": "Madhya Pradesh",
    "uttarpradesh": "Uttar Pradesh",
    "westbengal": "West Bengal",
    "tamilnadu": "Tamil Nadu",
    "chandigarh": "Chandigarh",
    "kerla": "Kerala",
}

class UniversalNormalizer:
    @staticmethod
    def clean_text(val):
        if not val or not isinstance(val, str): return ""
        val = unicodedata.normalize('NFKD', val).encode('ascii', 'ignore').decode('ascii')
        val = val.lower().strip()
        val = re.sub(r'\s+', ' ', val)
        val = re.sub(r'([,.])\1+', r'\1', val)
        return val

    @staticmethod
    def normalize_state(val):
        val = UniversalNormalizer.clean_text(val)
        # Remove anything not alphanumeric for strict matching
        val = re.sub(r'[^a-z0-9]', '', val)
        return STATE_MAP.get(val, val.title())

    @staticmethod
    def normalize_phone(val):
        if not val: return ""
        return re.sub(r'\D', '', str(val))

    @staticmethod
    def normalize_website(val):
        val = UniversalNormalizer.clean_text(val)
        val = re.sub(r'^https?://', '', val)
        val = re.sub(r'^www\.', '', val)
        return val.rstrip('/')

    @staticmethod
    def normalize_category(val):
        val = UniversalNormalizer.clean_text(val).rstrip('s') # Basic singularization
        return val.title()

    @classmethod
    def normalize_row(cls, row):
        return {
            "name": cls.clean_text(row.get("name")),
            "address": cls.clean_text(row.get("address")),
            "website": cls.normalize_website(row.get("website")),
            "phone_number": cls.normalize_phone(row.get("phone_number")),
            "reviews_count": row.get("reviews_count"),
            "reviews_average": row.get("reviews_average"),
            "category": cls.normalize_category(row.get("category")),
            "subcategory": cls.clean_text(row.get("subcategory")),
            "city": cls.clean_text(row.get("city")).title(),
            "state": cls.normalize_state(row.get("state")),
            "area": cls.clean_text(row.get("area")),
            "drive_folder_id": row.get("drive_folder_id"),
            "drive_folder_name": row.get("drive_folder_name"),
            "drive_file_id": row.get("drive_file_id"),
            "drive_file_name": row.get("drive_file_name"),
            "drive_file_path": row.get("drive_file_path"),
            "drive_uploaded_time": row.get("drive_uploaded_time"),
        }
