/**
 * ═══════════════════════════════════════════════════════════════════════════════
 *  NORMALIZATION ENGINE v1.0
 * ═══════════════════════════════════════════════════════════════════════════════
 * Pure view-layer logic to clean and aggregate messy drive data.
 */

const STATE_MAPPING = {
    // Andhra Pradesh
    "ANDHRA PRADESH": "ANDHRA PRADESH",
    "AANDHRAAPRADESH": "ANDHRA PRADESH",
    "ANDHRAPRADESH": "ANDHRA PRADESH",
    "ANDHRAPRADHESH": "ANDHRA PRADESH",
    "ANDHRA_PRADESH": "ANDHRA PRADESH",
    "ANDHRA PRADESH,": "ANDHRA PRADESH",

    // Arunachal Pradesh
    "ARUNACHAL PRADESH": "ARUNACHAL PRADESH",
    "ARUNACHALPRADESH": "ARUNACHAL PRADESH",
    "ARUNACHAL_PRADESH": "ARUNACHAL PRADESH",

    // Madhya Pradesh
    "MADHYA PRADESH": "MADHYA PRADESH",
    "MADHYAPRADESH": "MADHYA PRADESH",
    "MADHYA_PRADESH": "MADHYA PRADESH",

    // Uttar Pradesh
    "UTTAR PRADESH": "UTTAR PRADESH",
    "UTTARPRADESH": "UTTAR PRADESH",
    "UTTAR_PRADESH": "UTTAR PRADESH",

    // West Bengal
    "WEST BENGAL": "WEST BENGAL",
    "WESTBENGAL": "WEST BENGAL",
    "WEST_BENGAL": "WEST BENGAL",

    // Tamil Nadu
    "TAMIL NADU": "TAMIL NADU",
    "TAMILNADU": "TAMIL NADU",
    "TAMIL_NADU": "TAMIL NADU",

    // Himachal Pradesh
    "HIMACHAL PRADESH": "HIMACHAL PRADESH",
    "HIMACHALPRADESH": "HIMACHAL PRADESH",
    "HIMACHAL_PRADESH": "HIMACHAL PRADESH",

    // Jammu & Kashmir
    "JAMMU AND KASHMIR": "JAMMU AND KASHMIR",
    "JAMMUKASHMIR": "JAMMU AND KASHMIR",
    "JAMMU_KASHMIR": "JAMMU AND KASHMIR",
    "JAMMU&KASHMIR": "JAMMU AND KASHMIR",
    "JAMMU AND KASHMIR,": "JAMMU AND KASHMIR",

    // Chhattisgarh
    "CHHATTISGARH": "CHHATTISGARH",
    "CHATTISGARH": "CHHATTISGARH",
    "CHATTISHGARH": "CHHATTISGARH",

    // Maharashtra
    "MAHARASHTRA": "MAHARASHTRA",
    "MAHARASTRA": "MAHARASHTRA",
    "MAHARASHTRA,": "MAHARASHTRA",

    // Kerala
    "KERALA": "KERALA",
    "KERLA": "KERALA",
};

export const normalizeStateName = (rawState, rawCity = "") => {
    if (!rawState) return "UNKNOWN";
    let normalized = rawState.toUpperCase();
    // Aggressive cleanup: remove anything that isn't A-Z or a character we specifically handle
    normalized = normalized.replace(/[^A-Z0-9\s&_]/g, '');
    normalized = normalized.replace(/,/g, '');
    normalized = normalized.replace(/&/g, ' AND ');
    normalized = normalized.replace(/_/g, ' ');
    normalized = normalized.trim();
    normalized = normalized.replace(/\s+/g, ' '); // Collapse double spaces

    // Apply canonical mapping
    // Level 1: Exact Match (with collapsed spaces)
    if (STATE_MAPPING[normalized]) return STATE_MAPPING[normalized];

    // Level 2: Merged Words (No spaces)
    const noSpace = normalized.replace(/\s/g, '');
    if (STATE_MAPPING[noSpace]) return STATE_MAPPING[noSpace];

    // Level 3: Extra Typos (Double letters, soft characters)
    // We already have some in the mapping, but let's try a "skeleton" match
    // by removing common extra letters if needed, but for now, the map is better.

    // Level 4: City Fallback (Highest priority for "Unknown" or "Null")
    if ((normalized === "UNKNOWN" || normalized === "NULL" || normalized === "") && rawCity) {
        const cityUpper = rawCity.toUpperCase();
        for (const [key, val] of Object.entries(STATE_MAPPING)) {
            if (cityUpper.includes(key.replace(/\s/g, ''))) return val;
        }
    }

    return normalized;
};

const MASTER_CATEGORIES = [
    "Medical Store", "Chemist", "Pharma Store", "Clinic", "Dentist", "Doctor", "Hospital", "Pathology Laboratory",
    "Dietitians", "Blood Bank", "Ayurvedic Doctor", "Dermatologists", "Health Clinics", "Nursing Services",
    "Restaurant", "Restaurants", "Quick Bites Restaurants", "North Indian Restaurants", "Chinese Restaurants",
    "South Indian Restaurants", "Top Indian Restaurants", "Continental Restaurants", "Italian Restaurants",
    "American Restaurants", "Mughlai Restaurants", "Colombian Specialty Restaurants", "Chettinad Specialty Restaurants",
    "Biryani Restaurants", "Dessert Restaurants", "Breakfast Restaurants", "Burger Restaurants", "Pizza Places",
    "Juices Restaurants", "Walk-In Restaurants", "Restaurants with Table Booking", "Restaurants with WiFi",
    "Full Bar Available Restaurants", "Valet Available Restaurants", "Air Conditioned Restaurants", "Digital Payment-Friendly Restaurants",
    "Debit Card Payment Dining", "Credit Card Payment Restaurants", "Smoking Area Feature Restaurants",
    "Home Delivery Restaurants", "Pure Vegetarian Restaurants", "Casual Dining Spots", "Lunch Spots", "Top Dining Restaurants",
    "Top Beverage Spots", "Local ATM Locations", "Cafes", "Cafes with Takeaway Service", "Cafes with Indoor Seating",
    "Cafes with Outdoor Seating", "Free Parking Cafes", "Quick Bite Cafes", "Coffee Shop", "Tea Shop", "Ice Cream Parlor",
    "Ice Cream Parlors", "Bakery", "Sweet Shop", "Fast Food", "Punjabi Food", "Chinese Food", "South Indian Food",
    "Dhaba", "Food Court", "Tiffin Services", "Milk Parlor", "Fashion Store", "Grament Store", "Electronic Stores",
    "Supermarkets", "Mobile Store", "Gift Shop", "Boutique", "Accessory Stores", "Woman Accessory", "Man Accessory",
    "General Store", "Fruit and Vegetable Store", "Electrical Shop", "Handicraft Store", "Jewellery Shops",
    "Jewellery Showrooms", "Luggage and Bags", "Modular Kitchen", "Pet Store", "Stationery Shop", "Stationery Stores",
    "Furniture Store", "Top Furniture Dealers", "Top Jewellery Stores", "Top Clothing Stores", "Departmental Stores",
    "Organic Store", "Optical Shop", "Hardware and Electrical Shops", "Computer Hardware Stores", "Popular Mobile Phone Dealers",
    "Top Shoe Dealers", "Latest Designer Saree", "Top Textile Fabric Dealers", "Car Showroom", "Bike Showroom",
    "Car Service", "Car Accessories", "Top Car Accessories Dealers", "Auto Parts Dealers", "New Cars", "Used Cars",
    "Gas Station", "Petrol Pump", "Car Rental", "Taxi Service", "Top AC Dealers", "AC Service", "Hotel", "Hotels",
    "Hostel", "Resort", "Top Travel Agents", "Top Amusement Parks", "College", "School", "Play School", "Coaching",
    "Vocational Training", "Computer Training Institutes", "Language Class", "Dance Class", "Hobby Class", "Fitness Class",
    "Yoga", "Accountants", "Lawyers", "Legal Service", "Legal Services", "Tax Consultants", "Registration Consultants",
    "Insurance Services", "Architectural Services", "Interior Designers", "Website Designer", "Internet Website Designers",
    "IT Services", "SEO Services", "Advertising Agency", "Printing and Publishing Services", "Manufacturing Services",
    "Construction Material Suppliers", "Fabrication and Assembly Services", "Fabricators", "Placement Services",
    "Transporters", "Top Commercial Transporters", "Cleaning Service", "Laundry Service", "House Keeping Services",
    "Plumber Service", "Electricians", "Painting Contractors", "Pest Control Services", "Scrap Dealers", "Scrap Buyers",
    "Security System", "Event Planner", "Event Organizer", "DJs", "Florists", "Wedding Planners", "Mehndi Artist",
    "Videographer and Photographer", "Top Film Photography & Videography Services", "Club", "Pub", "Museum", "Kids Park",
    "Banquet Halls", "Body Massage Centers", "Beauty Spa", "Beauty Parlour", "Hobbies", "Real Estate", "Top Real Estate Agents",
    "List of Top Builders & Developers", "Flat", "Bungalow", "Bank", "Banks", "ATM", "Courier", "Packers and Movers",
    "Packers & Movers", "Computer & Laptop Repair & Services", "Shopping", "Caterer", "Grocery Delivery", "Food Delivery",
    "Internet Services", "Internet Providers", "Top Dentists", "Top Matrimonial Astrologers", "Popular Computer Training Institutes",
    "Top Builders", "AC Dealers", "Interior Designer", "Internet Designer", "Top Furniture", "Top Jewellery", "Local Pharmacies",
    "Local Doctors and Clinics", "Local Chartered Accountants", "Banks and ATM", "Restaurants with AC"
];

// Memoization cache for performance (O(n) matching)
const categoryCache = new Map();

/**
 * Robust Cleaning Logic
 */
const cleanCategoryString = (str) => {
    if (!str) return "";
    let cleaned = str.toLowerCase();
    cleaned = cleaned.replace(/,/g, ''); // Remove commas
    cleaned = cleaned.replace(/[._!?;:]/g, ' '); // Remove punctuation and underscores
    cleaned = cleaned.replace(/&/g, 'and'); // Replace & with and
    cleaned = cleaned.trim();
    cleaned = cleaned.replace(/\s+/g, ' '); // Collapse spaces
    return cleaned;
};

/**
 * Singular / Plural normalization helper
 */
const getSingularForm = (str) => {
    if (str.endsWith('ies')) return str.slice(0, -3) + 'y';
    if (str.endsWith('es')) return str.slice(0, -2);
    if (str.endsWith('s')) return str.slice(0, -1);
    return str;
};

export const normalizeCategory = (rawCategory) => {
    if (!rawCategory || rawCategory.trim() === "" || rawCategory.toUpperCase() === "NULL") {
        return "OTHER";
    }

    const originalRaw = rawCategory.trim();
    if (categoryCache.has(originalRaw)) return categoryCache.get(originalRaw);

    const cleanedRaw = cleanCategoryString(rawCategory);
    if (!cleanedRaw) return "OTHER";

    // Matching Algorithm
    let bestMatch = null;

    // 1. Exact Match Priority
    for (const master of MASTER_CATEGORIES) {
        const cleanedMaster = cleanCategoryString(master);
        if (cleanedRaw === cleanedMaster) {
            bestMatch = master;
            break;
        }
    }

    // 2. Word-Based Fuzzy Match (Strict rules)
    if (!bestMatch) {
        // Sort master categories by length descending to match most specific first
        const sortedMasters = [...MASTER_CATEGORIES].sort((a, b) => b.length - a.length);

        for (const master of sortedMasters) {
            const cleanedMaster = cleanCategoryString(master);
            const rawWords = cleanedRaw.split(' ');
            const masterWords = cleanedMaster.split(' ');

            // Rule: If raw starts with master words (e.g., "car service center" matches "car service")
            // Or if they share the same singular root
            if (cleanedRaw.startsWith(cleanedMaster) ||
                cleanedMaster.startsWith(cleanedRaw) ||
                getSingularForm(cleanedRaw) === getSingularForm(cleanedMaster)) {
                bestMatch = master;
                break;
            }

            // Word overlap logic: if the first few words match exactly
            const matchLen = Math.min(masterWords.length, rawWords.length);
            let wordsMatch = true;
            for (let i = 0; i < matchLen; i++) {
                if (getSingularForm(rawWords[i]) !== getSingularForm(masterWords[i])) {
                    wordsMatch = false;
                    break;
                }
            }
            if (wordsMatch && matchLen >= 1) {
                bestMatch = master;
                break;
            }
        }
    }

    const finalCategory = bestMatch || "OTHER";
    categoryCache.set(originalRaw, finalCategory);
    return finalCategory;
};
