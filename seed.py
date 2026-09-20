import os
import sys
import django
import random
import urllib.request
from decimal import Decimal
from django.core.files.base import ContentFile
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from categories.models import Category
from products.models import Product, ProductImage, ProductVariant, Brand, Review
from accounts.models import User

# --- 1. HIERARCHY & BRANDS ---
HIERARCHY = {
    "Electronics": {
        "Mobiles & Accessories": ["Smartphones", "Feature Phones", "Mobile Accessories", "Cases & Covers"],
        "Computers & Accessories": ["Laptops", "Desktops", "Monitors", "Keyboards", "Computer Accessories"],
        "Audio": ["Headphones", "Earbuds", "Speakers", "Home Audio"],
        "Cameras & Photography": ["DSLR", "Mirrorless", "Action Cameras", "Camera Accessories"],
        "Wearable Technology": ["Smart Watches", "Fitness Trackers", "VR Headsets"]
    },
    "Fashion": {
        "Men's Clothing": ["T-Shirts", "Shirts", "Men's Jeans", "Trousers", "Jackets"],
        "Women's Clothing": ["Dresses", "Tops", "Women's Jeans", "Activewear", "Ethnic Wear"],
        "Footwear": ["Men's Sneakers", "Women's Sneakers", "Formal Shoes", "Sports Shoes"],
        "Accessories": ["Watches", "Bags", "Wallets", "Sunglasses", "Belts"]
    },
    "Home & Kitchen": {
        "Kitchen Appliances": ["Microwaves", "Blenders", "Coffee Makers", "Air Fryers"],
        "Cookware": ["Pots & Pans", "Pressure Cookers", "Utensils"],
        "Furniture": ["Living Room", "Bedroom", "Office Furniture"],
        "Home Decor": ["Lighting", "Wall Art", "Rugs", "Clocks"]
    },
    "Beauty & Personal Care": {
        "Skincare": ["Face Wash", "Moisturizers", "Serums", "Sunscreens"],
        "Haircare": ["Shampoo", "Conditioners", "Hair Oils", "Styling"],
        "Makeup": ["Face", "Eyes", "Lips", "Nails"],
        "Grooming": ["Trimmers", "Shaving Kits", "Deodorants"]
    },
    "Sports & Fitness": {
        "Fitness Equipment": ["Dumbbells", "Resistance Bands", "Yoga Mats", "Treadmills"],
        "Outdoor Recreation": ["Tents", "Sleeping Bags", "Backpacks"],
        "Cycling": ["Bicycles", "Bike Helmets", "Cycling Gear"]
    },
    "Books": {
        "Fiction": ["Thrillers", "Romance", "Science Fiction", "Fantasy"],
        "Non-Fiction": ["Biographies", "Self-Help", "History", "Business"],
        "Academic": ["School Books", "College Textbooks", "Exam Preparation"]
    },
    "Grocery": {
        "Beverages": ["Coffee", "Tea", "Soft Drinks", "Juices"],
        "Snacks": ["Chips", "Biscuits", "Chocolates", "Nuts"],
        "Cooking Essentials": ["Oil", "Spices", "Rice", "Flour"]
    },
    "Automotive": {
        "Car Accessories": ["Car Covers", "Floor Mats", "Dash Cams"],
        "Bike Accessories": ["Cycling Helmets", "Riding Gloves", "Bike Covers"],
        "Car Care": ["Wash & Wax", "Microfiber Cloths", "Polish"]
    },
    "Toys & Games": {
        "Educational Toys": ["Building Blocks", "Science Kits", "Learning Pads"],
        "Action Figures": ["Superheroes", "Anime Figures", "Vehicles"],
        "Board Games": ["Strategy Games", "Family Games", "Puzzles"]
    },
    "Baby Products": {
        "Baby Care": ["Diapers", "Wipes", "Baby Lotions"],
        "Feeding": ["Bottles", "Bibs", "Breast Pumps"],
        "Nursery": ["Cribs", "Baby Monitors", "Bedding"]
    }
}

BRANDS_MAP = {
    "Apple": ["Smartphones", "Laptops", "Smart Watches", "Earbuds", "Tablets"],
    "Samsung": ["Smartphones", "Monitors", "Smart Watches", "Kitchen Appliances"],
    "Sony": ["Headphones", "Mirrorless", "Action Cameras", "Speakers", "Gaming"],
    "Nike": ["Men's Sneakers", "Women's Sneakers", "Sports Shoes", "Activewear"],
    "Adidas": ["Men's Sneakers", "Women's Sneakers", "Sports Shoes", "Activewear"],
    "Dell": ["Laptops", "Desktops", "Monitors"],
    "HP": ["Laptops", "Desktops", "Printers", "Computer Accessories"],
    "Philips": ["Kitchen Appliances", "Grooming", "Lighting"],
    "Puma": ["Men's Sneakers", "Women's Sneakers", "Sports Shoes", "Bags"],
    "Levi's": ["Jeans", "T-Shirts", "Shirts", "Jackets"],
    "L'Oreal": ["Haircare", "Skincare", "Makeup"],
    "Maybelline": ["Makeup", "Face", "Eyes", "Lips"],
    "Bose": ["Headphones", "Earbuds", "Speakers", "Home Audio"],
    "JBL": ["Headphones", "Earbuds", "Speakers", "Home Audio"],
    "Canon": ["DSLR", "Mirrorless", "Camera Accessories"],
    "Nikon": ["DSLR", "Mirrorless", "Camera Accessories"],
    "LG": ["Monitors", "Kitchen Appliances", "TVs"],
    "Prestige": ["Kitchen Appliances", "Cookware", "Pressure Cookers"],
    "Milton": ["Cookware", "Utensils"],
    "Fastrack": ["Watches", "Sunglasses", "Bags"],
    "Titan": ["Watches", "Sunglasses"],
    "Decathlon": ["Tents", "Sleeping Bags", "Bicycles", "Yoga Mats"],
    "Nivea": ["Skincare", "Deodorants", "Grooming"],
    "Pampers": ["Diapers", "Wipes", "Baby Care"],
    "Lego": ["Building Blocks", "Educational Toys"],
    "Mattel": ["Action Figures", "Board Games"],
    "Penguin": ["Fiction", "Non-Fiction", "Biographies"],
    "Nescafe": ["Coffee", "Beverages"],
    "Lays": ["Chips", "Snacks"],
    "Cadbury": ["Chocolates", "Snacks"],
    "3M": ["Car Care", "Wash & Wax", "Microfiber Cloths"]
}

# Generic fallback brands if category doesn't have a specific brand mapped
GENERIC_BRANDS = ["AmazonBasics", "Generic", "Solimo", "PremiumBrand"]

# --- 2. PRODUCT TEMPLATES ---
# We will use these high-quality templates and generate variants (colors, models) to reach 500+ products
PRODUCT_TEMPLATES = [
    {
        "cats": ["Smartphones"],
        "name": "{brand} Flagship Smartphone {suffix}",
        "desc": "Experience the ultimate performance with the {brand} flagship smartphone. Featuring a stunning OLED display, pro-grade camera system for perfect night shots, all-day battery life, and lightning-fast processor. Designed for those who demand the best in mobile technology.",
        "specs": {"Display": "6.7 inch OLED", "Camera": "50MP Triple System", "Battery": "5000mAh", "Processor": "Octa-core 5nm"},
        "base_price": 79999,
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=800",
        "tags": ["smartphone", "flagship", "premium", "5g", "mobile"]
    },
    {
        "cats": ["Laptops"],
        "name": "{brand} UltraBook Pro {suffix}",
        "desc": "Power through your workday with the {brand} UltraBook Pro. Featuring a stunning Retina display, lightning-fast SSD storage, and up to 18 hours of battery life. The ultra-thin aerospace-grade aluminum body makes it the perfect companion for professionals on the go.",
        "specs": {"Processor": "Intel Core i7 / M-Series", "RAM": "16GB Unified", "Storage": "512GB NVMe SSD", "Weight": "1.2 kg"},
        "base_price": 105000,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=800",
        "tags": ["laptop", "ultrabook", "professional", "work", "tech"]
    },
    {
        "cats": ["Headphones", "Earbuds"],
        "name": "{brand} Noise Cancelling Wireless Headphones {suffix}",
        "desc": "Immerse yourself in music with industry-leading Active Noise Cancellation. These {brand} wireless headphones feature plush ear cushions for all-day comfort, 30-hour battery life, and multipoint Bluetooth connectivity. Perfect for travel, work, and gaming.",
        "specs": {"Connectivity": "Bluetooth 5.2", "Battery": "30 Hours", "Feature": "Active Noise Cancellation", "Weight": "250g"},
        "base_price": 24999,
        "image_url": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?q=80&w=800",
        "tags": ["audio", "wireless", "headphones", "anc", "travel", "music"]
    },
    {
        "cats": ["Men's Sneakers", "Women's Sneakers", "Sports Shoes"],
        "name": "{brand} Performance Running Shoes {suffix}",
        "desc": "Push your limits with the {brand} Performance Running shoes. Engineered with responsive foam cushioning that absorbs impact and returns energy with every step. The breathable mesh upper keeps your feet cool during intense workouts or long city walks.",
        "specs": {"Material": "Breathable Mesh", "Sole": "Rubber Outsole", "Cushioning": "Responsive Foam", "Best For": "Running, Gym"},
        "base_price": 4999,
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=800",
        "tags": ["shoes", "running", "fitness", "sneakers", "sports", "activewear"]
    },
    {
        "cats": ["Jeans", "Trousers"],
        "name": "{brand} Classic Fit Denim Jeans {suffix}",
        "desc": "A timeless wardrobe staple. These {brand} classic fit jeans are crafted from premium stretch-denim for maximum comfort without losing their shape. Features a versatile mid-rise waist, classic 5-pocket styling, and durable hardware. Perfect for casual office wear or weekend outings.",
        "specs": {"Fit": "Classic / Slim", "Material": "98% Cotton, 2% Elastane", "Wash": "Machine Washable", "Style": "5-Pocket"},
        "base_price": 2599,
        "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=800",
        "tags": ["jeans", "denim", "clothing", "casual", "fashion"]
    },
    {
        "cats": ["T-Shirts", "Shirts", "Tops"],
        "name": "{brand} Essential Cotton T-Shirt {suffix}",
        "desc": "Upgrade your basics with the {brand} Essential Cotton T-Shirt. Made from 100% organic ring-spun cotton, this shirt offers an ultra-soft feel and a tailored fit. Preshrunk to ensure a perfect fit wash after wash. An absolute must-have for effortless everyday style.",
        "specs": {"Material": "100% Organic Cotton", "Fit": "Regular Fit", "Neckline": "Crew Neck", "Care": "Machine wash cold"},
        "base_price": 999,
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?q=80&w=800",
        "tags": ["tshirt", "casual", "cotton", "summer", "essentials"]
    },
    {
        "cats": ["Watches", "Smart Watches"],
        "name": "{brand} Premium Chronograph Watch {suffix}",
        "desc": "Make a statement with this elegant {brand} chronograph watch. Featuring a durable stainless steel case, scratch-resistant sapphire crystal glass, and water resistance up to 50 meters. The perfect blend of sophisticated design and reliable timekeeping for any occasion.",
        "specs": {"Case": "Stainless Steel", "Glass": "Sapphire Crystal", "Movement": "Quartz / Smart", "Water Resistance": "50m"},
        "base_price": 8500,
        "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?q=80&w=800",
        "tags": ["watch", "accessories", "luxury", "timepiece", "gift"]
    },
    {
        "cats": ["Bags", "Backpacks", "Wallets"],
        "name": "{brand} Urban Travel Backpack {suffix}",
        "desc": "The ultimate everyday carry. The {brand} Urban Travel Backpack features a padded laptop sleeve, weather-resistant exterior, and ergonomic shoulder straps for all-day comfort. Thoughtful organizational pockets keep your tech, water bottle, and daily essentials perfectly organized.",
        "specs": {"Material": "Water-resistant Nylon", "Capacity": "24 Liters", "Laptop Sleeve": "Fits up to 15.6 inch", "Weight": "0.8 kg"},
        "base_price": 3299,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=800",
        "tags": ["bag", "backpack", "travel", "office", "accessories"]
    },
    {
        "cats": ["Kitchen Appliances", "Coffee Makers", "Blenders"],
        "name": "{brand} Professional Kitchen Series {suffix}",
        "desc": "Elevate your culinary skills with the {brand} Professional appliance series. Built with powerful motors and premium stainless steel components, this appliance is designed to handle tough ingredients and daily use. Easy to clean and looks beautiful on any kitchen counter.",
        "specs": {"Power": "1000W / 15Bar", "Material": "Stainless Steel / BPA-Free", "Warranty": "2 Years", "Voltage": "220-240V"},
        "base_price": 6499,
        "image_url": "https://images.unsplash.com/photo-1585237833075-8495a85ccb6b?q=80&w=800",
        "tags": ["kitchen", "home", "appliances", "cooking", "chef"]
    },
    {
        "cats": ["Furniture", "Living Room", "Office Furniture"],
        "name": "{brand} Ergonomic Design Series {suffix}",
        "desc": "Transform your space with {brand}. Designed with both aesthetics and supreme comfort in mind. Crafted from premium materials that ensure longevity while providing optimal support. The minimalist design seamlessly integrates into modern homes and professional workspaces.",
        "specs": {"Material": "Premium Fabric / Wood / Steel", "Assembly": "Required (Tool Included)", "Warranty": "5 Years", "Dimensions": "Standard"},
        "base_price": 12500,
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=800",
        "tags": ["furniture", "home", "decor", "interior", "comfort"]
    },
    {
        "cats": ["Skincare", "Face Wash", "Moisturizers"],
        "name": "{brand} Revitalizing Skincare {suffix}",
        "desc": "Reveal your natural glow with {brand}. Formulated with dermatologically tested ingredients, hydrating hyaluronic acid, and essential vitamins. This lightweight formula absorbs quickly without leaving a greasy residue, providing 24-hour hydration and protection against environmental stressors.",
        "specs": {"Volume": "100ml / 50g", "Skin Type": "All Skin Types", "Key Ingredients": "Vitamin C, Hyaluronic Acid", "Cruelty-Free": "Yes"},
        "base_price": 899,
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=800",
        "tags": ["beauty", "skincare", "glow", "cosmetics", "personal care"]
    },
    {
        "cats": ["Fitness Equipment", "Yoga Mats", "Dumbbells"],
        "name": "{brand} Pro Fitness Series {suffix}",
        "desc": "Build your home gym with the {brand} Pro Fitness Series. Engineered for durability and maximum performance. Whether you're doing high-intensity interval training, strength conditioning, or recovery yoga, this equipment is designed to help you achieve your fitness goals safely and effectively.",
        "specs": {"Material": "High-Density / Commercial Grade", "Durability": "Heavy Duty", "Usage": "Home / Gym", "Warranty": "1 Year"},
        "base_price": 1999,
        "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?q=80&w=800",
        "tags": ["fitness", "gym", "workout", "sports", "health"]
    },
    {
        "cats": ["Fiction", "Non-Fiction", "Academic"],
        "name": "{brand} Bestseller Edition: {suffix}",
        "desc": "Dive into the world of knowledge and imagination. This bestselling edition features high-quality print, crisp typography, and premium binding. A must-read that has captured the attention of millions worldwide. Add this masterpiece to your personal library today.",
        "specs": {"Format": "Paperback / Hardcover", "Language": "English", "Publisher": "{brand}", "Pages": "300+"},
        "base_price": 499,
        "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=800",
        "tags": ["books", "reading", "bestseller", "education", "literature"]
    }
]

# Generic fallback template
GENERIC_TEMPLATE = {
    "name": "{brand} Premium {child_cat} {suffix}",
    "desc": """High quality {child_cat} from {brand}. Designed with premium materials and precision engineering to deliver outstanding performance and reliability.

Key Features:
• Premium build quality
• Elegant modern design
• High durability
• Exceptional value for money

Perfect for everyday use.""",
    "specs": {"Quality": "Premium", "Durability": "High", "Warranty": "1 Year Standard", "Authenticity": "100% Genuine"},
    "base_price": 1500,
    "image_url": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?q=80&w=800",
    "tags": ["premium", "bestseller", "quality", "new", "essential"]
}

SUFFIXES = ["Pro", "Max", "Ultra", "Lite", "Edition", "Series X", "V2", "Essential", "Classic", "Premium", "Signature", "Advanced", "Plus", "Gen 2"]

# Image Cache to avoid downloading the same URL multiple times
IMAGE_CACHE = {}

def download_image(url, filename):
    if url in IMAGE_CACHE:
        return IMAGE_CACHE[url]
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=5)
        image_data = response.read()
        IMAGE_CACHE[url] = image_data
        return image_data
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return None

def seed_db(reset=False, num_products=500):
    if reset:
        print("Resetting database (Products, Categories, Brands, Reviews)...")
        Review.objects.all().delete()
        ProductImage.objects.all().delete()
        ProductVariant.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Brand.objects.all().delete()
        print("Reset complete.")

    print("--- 1. Creating/Updating Brands ---")
    brand_objs = {}
    touched_brand_ids = set()
    all_brand_names = list(BRANDS_MAP.keys()) + GENERIC_BRANDS
    for b_name in all_brand_names:
        slug = b_name.lower().replace(" ", "-").replace("'", "")
        brand, _ = Brand.objects.update_or_create(
            slug=slug, 
            defaults={'name': b_name}
        )
        brand_objs[b_name] = brand
        touched_brand_ids.add(brand.id)

    print("--- 2. Creating/Updating Categories (Amazon-style Hierarchy) ---")
    child_categories = []
    touched_category_ids = set()
    
    for main_name, sub_data in HIERARCHY.items():
        main_slug = main_name.lower().replace(" & ", "-").replace(" ", "-").replace("'", "")
        main_cat, _ = Category.objects.update_or_create(
            slug=main_slug, 
            defaults={
                'name': main_name,
                'parent': None,
                'is_active': True,
                'display_order': 0
            }
        )
        touched_category_ids.add(main_cat.id)
        
        for sub_name, children in sub_data.items():
            sub_slug = f"{main_cat.slug}-{sub_name.lower().replace(' & ', '-').replace(' ', '-').replace("'", "")}"
            sub_cat, _ = Category.objects.update_or_create(
                slug=sub_slug, 
                defaults={
                    'name': sub_name,
                    'parent': main_cat,
                    'is_active': True
                }
            )
            touched_category_ids.add(sub_cat.id)
            
            for child_name in children:
                child_slug = f"{sub_cat.slug}-{child_name.lower().replace(' & ', '-').replace(' ', '-').replace("'", "")}"
                child_cat, _ = Category.objects.update_or_create(
                    slug=child_slug, 
                    defaults={
                        'name': child_name,
                        'parent': sub_cat,
                        'is_active': True
                    }
                )
                touched_category_ids.add(child_cat.id)
                child_categories.append({
                    "main": main_name,
                    "sub": sub_name,
                    "child": child_cat
                })

    print(f"Total Child Categories created/updated: {len(child_categories)}")

    print("--- 3. Creating Demo Users (for Reviews) ---")
    users = []
    for i in range(1, 11):
        user, _ = User.objects.get_or_create(email=f"shopper{i}@aeon.com", defaults={'username': f"shopper{i}", 'first_name': f"Shopper{i}", 'last_name': 'Verified'})
        users.append(user)

    print(f"--- 4. Creating/Updating {num_products} Products ---")
    created_count = 0
    updated_count = 0
    touched_product_ids = set()
    
    # Use deterministic random seed so sync operates on exactly the same identifiers
    random.seed(42)
    
    # Pre-calculate templates to child categories
    cat_to_template = {}
    for item in child_categories:
        c_name = item["child"].name
        matched_tpl = GENERIC_TEMPLATE
        for tpl in PRODUCT_TEMPLATES:
            if c_name in tpl["cats"]:
                matched_tpl = tpl
                break
        cat_to_template[c_name] = matched_tpl

    for i in range(num_products):
        cat_info = random.choice(child_categories)
        main_name = cat_info["main"]
        child_cat = cat_info["child"]
        child_name = child_cat.name
        
        # Pick a valid brand
        valid_brands = [b for b, cats in BRANDS_MAP.items() if child_name in cats or main_name in cats]
        if not valid_brands:
            valid_brands = GENERIC_BRANDS
        b_name = random.choice(valid_brands)
        brand = brand_objs[b_name]
        
        tpl = cat_to_template[child_name]
        
        suffix = random.choice(SUFFIXES)
        # Format strings
        product_name = tpl["name"].format(brand=b_name, child_cat=child_name, suffix=suffix) + f" {random.randint(10, 99)}"
        description = tpl["desc"].format(brand=b_name, child_cat=child_name)
        
        # Specifications (Append to description or short_desc)
        specs_text = "\n\nSpecifications:\n"
        for k, v in tpl["specs"].items():
            specs_text += f"• {k}: {v}\n"
            
        full_description = description + specs_text
        short_desc = description[:150] + "..."
        
        # Slug is completely deterministic based on the loop index `i`
        slug = f"aeon-prod-{i}"
        sku = f"{b_name[:3].upper()}{child_name[:3].upper()}{str(i).zfill(5)}"
        
        # Pricing
        variance = random.uniform(0.7, 1.5)
        base_price = int(tpl["base_price"] * variance)
        base_price = (base_price // 10) * 10 + 9
        
        discount_price = None
        if random.random() > 0.4: # 60% chance of discount
            discount = int(base_price * random.uniform(0.1, 0.4))
            discount_price = base_price
            base_price = base_price - discount
            base_price = (base_price // 10) * 10 + 9 # Sale price
        
        # Stock
        stock_scenario = random.random()
        if stock_scenario > 0.95:
            stock = 0 # 5% Out of stock
        elif stock_scenario > 0.85:
            stock = random.randint(1, 5) # 10% Low stock
        else:
            stock = random.randint(20, 200) # Normal stock
            
        stock_status = 'out_of_stock' if stock == 0 else 'low_stock' if stock < 10 else 'in_stock'
        
        meta_title = f"Buy {product_name} Online | AEON"
        meta_desc = f"Shop {product_name} at the best price. {short_desc}"
        
        # Create or Update Product
        try:
            p, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': product_name,
                    'sku': sku,
                    'category': child_cat,
                    'brand': brand,
                    'description': full_description,
                    'short_description': short_desc,
                    'price': Decimal(base_price),
                    'discount_price': Decimal(discount_price) if discount_price else None,
                    'stock_quantity': stock,
                    'stock_status': stock_status,
                    'status': 'published',
                    'visibility': 'visible',
                    'is_featured': random.random() > 0.9,
                    'is_bestseller': random.random() > 0.8,
                    'is_new_arrival': random.random() > 0.7,
                }
            )
            
            touched_product_ids.add(p.id)
            
            if created:
                created_count += 1
                # Download and save image only on create, don't overwrite if syncing existing products
                img_data = download_image(tpl["image_url"], f"{slug}.jpg")
                if img_data:
                    img = ProductImage(product=p, is_main=True, alt_text=product_name)
                    img.image.save(f"{slug}.jpg", ContentFile(img_data), save=True)
                
                # Variants (for Fashion)
                if main_name == "Fashion" and child_name in ["T-Shirts", "Shirts", "Dresses", "Men's Sneakers", "Women's Sneakers"]:
                    sizes = ['S', 'M', 'L', 'XL'] if 'Sneakers' not in child_name else ['UK 7', 'UK 8', 'UK 9', 'UK 10']
                    for size in sizes:
                        ProductVariant.objects.create(
                            product=p,
                            name=f"{product_name} - {size}",
                            sku=f"{sku}-{size.replace(' ', '')}",
                            stock=random.randint(0, 50),
                            attributes={'Size': size}
                        )
            else:
                updated_count += 1

            # Provide reviews randomly on create/update to flesh out data
            num_reviews = random.randint(0, 2)
            for _ in range(num_reviews):
                user = random.choice(users)
                if not Review.objects.filter(product=p, user=user).exists():
                    Review.objects.create(
                        product=p,
                        user=user,
                        rating=random.choices([1, 2, 3, 4, 5], weights=[5, 5, 10, 30, 50])[0],
                        comment=random.choice(["Highly recommended.", "Great quality.", "Exactly as described."])
                    )

            if (created_count + updated_count) > 0 and (created_count + updated_count) % 50 == 0:
                print(f"  ... synced {created_count + updated_count} products")
                
        except Exception as e:
            print(f"Error creating/updating product {product_name}: {e}")

    # --- 5. Clean up Orphans (Strict Sync) ---
    if not reset:
        print("--- 5. Cleaning up removed/orphaned records ---")
        deleted_prods, _ = Product.objects.exclude(id__in=touched_product_ids).delete()
        print(f"Removed {deleted_prods} orphaned products.")
        
        deleted_cats, _ = Category.objects.exclude(id__in=touched_category_ids).delete()
        print(f"Removed {deleted_cats} orphaned categories.")
        
        deleted_brands, _ = Brand.objects.exclude(id__in=touched_brand_ids).delete()
        print(f"Removed {deleted_brands} orphaned brands.")

    print("\n===========================================")
    print("       AEON DATABASE SYNC COMPLETE     ")
    print("===========================================")
    print(f"Products Created:     {created_count}")
    print(f"Products Updated:     {updated_count}")
    print("Database is strictly synced with seed.py configuration.")
    print("===========================================\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed the AEON E-commerce Database")
    parser.add_argument('--reset', action='store_true', help="Clear existing catalog before seeding")
    parser.add_argument('--count', type=int, default=500, help="Number of products to generate")
    args = parser.parse_args()
    
    seed_db(reset=args.reset, num_products=args.count)
