import os
from google import genai
from dotenv import load_dotenv
import json

load_dotenv()

def get_client():
    
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def scan_receipt(image_file):
    client = get_client()
    
    prompt = """
    Analyze this receipt image from an Israeli supermarket. 
    1. Extract the food items, their quantities, and categories.
    2. The names on the receipt might be abbreviated Hebrew or English. 
    3. Translate or convert the names to clear English product names.
    4. If you see a word you don't recognize, do not guess a random food name.
    
    Return the data strictly in JSON format:
    [{"product_name": "item name", "quantity": number, "category": "Dairy/Meat/Veggies/etc", "protein_per_unit": estimated_grams}]
    """
    
    try:
        # בגרסה החדשה מעבירים את ה-bytes ישירות או דרך אובייקט PIL
        image_data = image_file.getvalue()
        
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[prompt, genai.types.Part.from_bytes(data=image_data, mime_type="image/jpeg")]
        )
        
        # חילוץ ה-JSON מהטקסט
        text = response.text
        start = text.find('[')
        end = text.rfind(']') + 1
        return json.loads(text[start:end])
        
    except Exception as e:
        print(f"Error calling Gemini 3.1: {e}")
        return None

def get_ai_recipes(items_list):
  
    client = get_client()
    
    products_string = ", ".join(items_list)
    prompt = f"""
    I have the following ingredients in my pantry: {products_string}.
    Please suggest 2 simple and healthy recipes I can make with these.
    Focus on high protein if possible. 
    Format the response in a clear way with 'Ingredients' and 'Instructions'.
    Keep it concise.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Could not generate recipes: {e}"