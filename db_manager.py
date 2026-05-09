import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np
import bcrypt
from bson.objectid import ObjectId


load_dotenv()

class PantryDB:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri, tlsCAFile=certifi.where())
        self.db = self.client['SmartPantryDB']
        self.inventory = self.db['inventory']
        self.logs = self.db['consumption_logs']
        
        self.users = self.db['users']
        self.shopping_list_col = self.db['shopping_list']

    def add_item(self, user_id, name, category, quantity, unit, protein=0, expiry_date=None):
        """Add a new item to the inventory (Updated with user_id)"""
        item = {
            "user_id": user_id, 
            "product_name": name,
            "category": category,
            "current_qty": quantity,
            "unit": unit,
            "protein_per_unit": protein,
            "expiry_date": expiry_date,
            "last_updated": datetime.now()
        }
        result = self.inventory.insert_one(item)
        print(f"✅ the item '{name}' was added successfully!")
        return result.inserted_id

    def get_all_items(self, user_id):
        """Get items only for the logged-in user"""
        return list(self.inventory.find({"user_id": user_id}))

    def get_low_stock(self, user_id, threshold=2):
        """Get low stock items for specific user"""
        query = {"user_id": user_id, "current_qty": {"$lt": threshold}}
        return list(self.inventory.find(query))

    def update_item_quantity(self, user_id, name, change):
        """Update quantity (Scoped to user)"""
        query = {"user_id": user_id, "product_name": name}
        update = {"$inc": {"current_qty": change}, "$set": {"last_updated": datetime.now()}}
        result = self.inventory.update_one(query, update)
        return result.modified_count > 0

    def delete_item(self, user_id, name):
        """Delete item (Scoped to user)"""
        query = {"user_id": user_id, "product_name": name}
        result = self.inventory.delete_one(query)
        return result.deleted_count > 0

    def calculate_total_protein(self, user_id):
        """Calculate protein for specific user"""
        items = self.get_all_items(user_id)
        total_protein = 0
        for item in items:
            qty = item.get('current_qty', 0)
            prot = item.get('protein_per_unit', 0)
            total_protein += (qty * prot)
        return total_protein

    def log_action(self, user_id, name, action_type, quantity):
        """Log action with user_id"""
        log_entry = {
            "user_id": user_id,
            "product_name": name,
            "action": action_type,
            "quantity": quantity,
            "timestamp": datetime.now()
        }
        self.logs.insert_one(log_entry)

    def add_to_shopping_list(self, user_id, item_name, quantity=1):
        """Add to list (Scoped to user)"""
        self.shopping_list_col.update_one(
            {"user_id": user_id, "item": item_name},
            {"$inc": {"quantity": quantity}},
            upsert=True
        )

    def get_shopping_list(self, user_id):
        """Get list for specific user"""
        return list(self.shopping_list_col.find({"user_id": user_id}))

    def clear_shopping_list(self, user_id):
        """Clear list only for current user"""
        self.shopping_list_col.delete_many({"user_id": user_id})

    def remove_from_shopping_list(self, user_id, item_name):
        """Remove item (Scoped to user)"""
        self.shopping_list_col.delete_one({"user_id": user_id, "item": item_name})

    def update_shopping_list_item(self, user_id, old_name, new_name, new_quantity):
        """Update list item (Scoped to user)"""
        self.shopping_list_col.update_one(
            {"user_id": user_id, "item": old_name},
            {"$set": {"item": new_name, "quantity": new_quantity}}
        )

    def get_expired_items(self, user_id):
        """Get expired items for specific user"""
        today = datetime.now()
        return list(self.inventory.find({"user_id": user_id, "expiry_date": {"$lt": today}}))

    def move_to_pantry(self, user_id, item_name, quantity):
        """Move from list to pantry (Scoped to user)"""
        existing_item = self.inventory.find_one({
            "user_id": user_id,
            "product_name": {"$regex": f"^{item_name}$", "$options": "i"}
        })
        
        if existing_item:
            self.update_item_quantity(user_id, existing_item['product_name'], quantity)
        else:
            default_expiry = datetime.now() + timedelta(days=7)
            self.add_item(user_id, item_name, "Other", quantity, "units", 0, default_expiry)
        
        self.remove_from_shopping_list(user_id, item_name)

    def predict_days_remaining(self, user_id, item_name):
        """ML prediction (Scoped to user)"""
        current_item = self.inventory.find_one({"user_id": user_id, "product_name": item_name})
        if not current_item:
            return None
            
        logs = list(self.logs.find({"user_id": user_id, "product_name": item_name, "action": "consumed"}))
        
        if len(logs) >= 3:
            try:
                first_log_time = logs[0]['timestamp'].timestamp()
                X = np.array([(l['timestamp'].timestamp() - first_log_time) for l in logs]).reshape(-1, 1)
                y = np.array([l['quantity'] for l in logs])

                model = LinearRegression().fit(X, y)
                rate_per_second = model.coef_[0]
                
                if rate_per_second > 0:
                    days_left = current_item['current_qty'] / (rate_per_second * 86400)
                    return round(days_left)
            except:
                pass

        category_defaults = {"Dairy": 7, "Meat": 3, "Veggies": 5, "Dry Goods": 30, "Other": 10}
        cat = current_item.get('category', 'Other')
        return category_defaults.get(cat, 10)

    def seed_demo_data(self, user_id):
        """Inject demo data for current user"""
        product_name = "Chicken Breast (Demo)"
        self.inventory.delete_one({"user_id": user_id, "product_name": product_name})
        self.logs.delete_many({"user_id": user_id, "product_name": product_name})
        
        self.add_item(user_id, product_name, "Meat", 10, "units", 25, datetime.now() + timedelta(days=5))
        
        for i in range(5, 2, -1):
            log_time = datetime.now() - timedelta(days=i)
            self.logs.insert_one({
                "user_id": user_id, "product_name": product_name,
                "action": "consumed", "quantity": 1, "timestamp": log_time
            })
        return product_name
    
    def create_user(self, username, password):
        if self.users.find_one({"username": username}):
            return False
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users.insert_one({"username": username, "password": hashed_password})
        return True

    def authenticate_user(self, username, password):
        user = self.users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return user
        return None
    def get_user_by_id(self, user_id):
        try:
            return self.db.users.find_one({"_id": ObjectId(user_id)})
        except:
            return None

if __name__ == "__main__":
    db = PantryDB()
    print("Database connection test complete.")