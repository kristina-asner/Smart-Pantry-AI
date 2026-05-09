import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def scan_receipt(image_file):
    # Use Gemini 3.1 Flash Lite for receipt analysis
    model = genai.GenerativeModel(model_name="models/gemini-3.1-flash-lite")
    
    prompt = """
    Analyze this receipt image from an Israeli supermarket. 
    1. Extract the food items, their quantities, and categories.
    2. The names on the receipt might be abbreviated Hebrew or English. 
    3. Translate or convert the names to clear English product names (e.g., if it says 'Milk 3%', write 'Milk 3%').
    4. If you see a word you don't recognize, do not guess a random food name like 'Cinnabon' unless it's clearly written.
    
    Return the data strictly in JSON format:
    [{"product_name": "item name", "quantity": number, "category": "Dairy/Meat/Veggies/etc", "protein_per_unit": estimated_grams}]
    """
    
    image_parts = [
        {
            "mime_type": "image/jpeg",
            "data": image_file.getvalue()
        }
    ]
    
    try:
        response = model.generate_content([prompt, image_parts[0]])
        # Gemini's response may contain extra text, so we need to extract the JSON part
        text = response.text
        start = text.find('[')
        end = text.rfind(']') + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f"Error calling Gemini 3.1: {e}")
        return None

def get_ai_recipes(items_list):
    """Suggest recipes based on the current pantry items using Gemini 3.1 Flash Lite"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    # prompt to get recipes based on pantry items
    products_string = ", ".join(items_list)
    prompt = f"""
    I have the following ingredients in my pantry: {products_string}.
    Please suggest 2 simple and healthy recipes I can make with these.
    Focus on high protein if possible. 
    Format the response in a clear way with 'Ingredients' and 'Instructions'.
    Keep it concise.
    """
    response = model.generate_content(prompt)
    return response.text