"""
API Tester Module
-----------------
"""

import google.generativeai as genai


def test_api_connection(api_key: str, model_name: str) -> dict:
    try:
        clean_api_key = api_key.strip()
        genai.configure(api_key=clean_api_key)
        model = genai.GenerativeModel(model_name)
        
        test_prompt = "Reply with exactly: 'API is working perfectly!'"
        response = model.generate_content(test_prompt)
        
        if response and response.text:
            return {
                "success": True,
                "message": f"✅ API কাজ করছে! Model: {model_name}",
                "response": response.text.strip()
            }
        else:
            return {"success": False, "message": "❌ Response পাওয়া যায়নি", "response": ""}
    
    except Exception as e:
        error_msg = str(e)
        
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return {"success": False, "message": "❌ API Key ভুল!", "response": error_msg}
        elif "not found" in error_msg.lower() or "404" in error_msg:
            return {"success": False, "message": f"❌ Model '{model_name}' পাওয়া যায়নি।", "response": error_msg}
        elif "quota" in error_msg.lower() or "429" in error_msg:
            return {"success": False, "message": "❌ API Quota শেষ!", "response": error_msg}
        else:
            return {"success": False, "message": f"❌ সমস্যা: {error_msg[:200]}", "response": error_msg}


def list_available_models(api_key: str) -> list:
    try:
        clean_api_key = api_key.strip()
        genai.configure(api_key=clean_api_key)
        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(m.name.replace("models/", ""))
        return models
    except Exception as e:
        return [f"Error: {str(e)}"]