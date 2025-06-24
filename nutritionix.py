import json
import httpx
from typing import List
from utils import get_nutritionix_headers, NUTRITIONIX_BASE_URL
from mcp_server import mcp

@mcp.tool()
async def search_foods(query: str, limit: int = 10) -> str:
    # ... existing code ...
    if limit > 50:
        limit = 50
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NUTRITIONIX_BASE_URL}/search/instant",
                headers=get_nutritionix_headers(),
                params={"query": query, "detailed": True}
            )
            response.raise_for_status()
            data = response.json()
            results = {"query": query, "common_foods": [], "branded_foods": []}
            if "common" in data:
                for food in data["common"][:limit//2]:
                    results["common_foods"].append({
                        "food_name": food.get("food_name"),
                        "serving_unit": food.get("serving_unit"),
                        "tag_name": food.get("tag_name"),
                        "tag_id": food.get("tag_id")
                    })
            if "branded" in data:
                for food in data["branded"][:limit//2]:
                    results["branded_foods"].append({
                        "food_name": food.get("food_name"),
                        "brand_name": food.get("brand_name"),
                        "serving_unit": food.get("serving_unit"),
                        "nf_calories": food.get("nf_calories"),
                        "nix_brand_id": food.get("nix_brand_id"),
                        "nix_item_id": food.get("nix_item_id")
                    })
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching foods: {str(e)}"

@mcp.tool()
async def get_food_nutrients(food_name: str, quantity: float = 1.0, unit: str = "serving") -> str:
    # ... existing code ...
    if quantity != 1.0 or unit != "serving":
        query = f"{quantity} {unit} {food_name}"
    else:
        query = food_name
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NUTRITIONIX_BASE_URL}/natural/nutrients",
                headers=get_nutritionix_headers(),
                json={"query": query}
            )
            response.raise_for_status()
            data = response.json()
            if "foods" not in data or not data["foods"]:
                return f"No nutritional information found for: {query}"
            food = data["foods"][0]
            nutrition_info = {
                "food_name": food.get("food_name"),
                "brand_name": food.get("brand_name"),
                "serving_qty": food.get("serving_qty"),
                "serving_unit": food.get("serving_unit"),
                "serving_weight_grams": food.get("serving_weight_grams"),
                "calories": food.get("nf_calories"),
                "macronutrients": {
                    "total_fat": f"{food.get('nf_total_fat', 0)}g",
                    "saturated_fat": f"{food.get('nf_saturated_fat', 0)}g",
                    "cholesterol": f"{food.get('nf_cholesterol', 0)}mg",
                    "sodium": f"{food.get('nf_sodium', 0)}mg",
                    "total_carbohydrate": f"{food.get('nf_total_carbohydrate', 0)}g",
                    "dietary_fiber": f"{food.get('nf_dietary_fiber', 0)}g",
                    "sugars": f"{food.get('nf_sugars', 0)}g",
                    "protein": f"{food.get('nf_protein', 0)}g"
                },
                "vitamins_minerals": {
                    "potassium": f"{food.get('nf_potassium', 0)}mg",
                    "phosphorus": f"{food.get('nf_phosphorus', 0)}mg"
                }
            }
            if food.get("photo", {}).get("thumb"):
                nutrition_info["photo_url"] = food["photo"]["thumb"]
            return json.dumps(nutrition_info, indent=2)
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting nutritional information: {str(e)}"

@mcp.tool()
async def compare_foods(food1: str, food2: str, quantity: float = 1.0, unit: str = "serving") -> str:
    # ... existing code ...
    async with httpx.AsyncClient() as client:
        try:
            if quantity != 1.0 or unit != "serving":
                query1 = f"{quantity} {unit} {food1}"
                query2 = f"{quantity} {unit} {food2}"
            else:
                query1 = food1
                query2 = food2
            response1 = await client.post(
                f"{NUTRITIONIX_BASE_URL}/natural/nutrients",
                headers=get_nutritionix_headers(),
                json={"query": query1}
            )
            response2 = await client.post(
                f"{NUTRITIONIX_BASE_URL}/natural/nutrients",
                headers=get_nutritionix_headers(),
                json={"query": query2}
            )
            response1.raise_for_status()
            response2.raise_for_status()
            data1 = response1.json()
            data2 = response2.json()
            if not data1.get("foods") or not data2.get("foods"):
                return "Could not find nutritional information for one or both foods"
            food1_data = data1["foods"][0]
            food2_data = data2["foods"][0]
            comparison = {
                "comparison_query": f"{query1} vs {query2}",
                "food1": {
                    "name": food1_data.get("food_name"),
                    "calories": food1_data.get("nf_calories", 0),
                    "protein": food1_data.get("nf_protein", 0),
                    "carbs": food1_data.get("nf_total_carbohydrate", 0),
                    "fat": food1_data.get("nf_total_fat", 0),
                    "fiber": food1_data.get("nf_dietary_fiber", 0),
                    "sodium": food1_data.get("nf_sodium", 0)
                },
                "food2": {
                    "name": food2_data.get("food_name"),
                    "calories": food2_data.get("nf_calories", 0),
                    "protein": food2_data.get("nf_protein", 0),
                    "carbs": food2_data.get("nf_total_carbohydrate", 0),
                    "fat": food2_data.get("nf_total_fat", 0),
                    "fiber": food2_data.get("nf_dietary_fiber", 0),
                    "sodium": food2_data.get("nf_sodium", 0)
                },
                "differences": {
                    "calories": food2_data.get("nf_calories", 0) - food1_data.get("nf_calories", 0),
                    "protein": food2_data.get("nf_protein", 0) - food1_data.get("nf_protein", 0),
                    "carbs": food2_data.get("nf_total_carbohydrate", 0) - food1_data.get("nf_total_carbohydrate", 0),
                    "fat": food2_data.get("nf_total_fat", 0) - food1_data.get("nf_total_fat", 0),
                    "fiber": food2_data.get("nf_dietary_fiber", 0) - food1_data.get("nf_dietary_fiber", 0),
                    "sodium": food2_data.get("nf_sodium", 0) - food1_data.get("nf_sodium", 0)
                }
            }
            return json.dumps(comparison, indent=2)
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error comparing foods: {str(e)}"

@mcp.tool()
async def analyze_meal(foods_list: List[str], meal_name: str = "Custom Meal") -> str:
    # ... existing code ...
    async with httpx.AsyncClient() as client:
        try:
            meal_query = ", ".join(foods_list)
            response = await client.post(
                f"{NUTRITIONIX_BASE_URL}/natural/nutrients",
                headers=get_nutritionix_headers(),
                json={"query": meal_query}
            )
            response.raise_for_status()
            data = response.json()
            if "foods" not in data or not data["foods"]:
                return f"No nutritional information found for meal: {meal_query}"
            totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0, "sugar": 0}
            food_breakdown = []
            for food in data["foods"]:
                food_info = {
                    "name": food.get("food_name"),
                    "quantity": food.get("serving_qty"),
                    "unit": food.get("serving_unit"),
                    "calories": food.get("nf_calories", 0),
                    "protein": food.get("nf_protein", 0),
                    "carbs": food.get("nf_total_carbohydrate", 0),
                    "fat": food.get("nf_total_fat", 0),
                    "fiber": food.get("nf_dietary_fiber", 0),
                    "sodium": food.get("nf_sodium", 0),
                    "sugar": food.get("nf_sugars", 0)
                }
                food_breakdown.append(food_info)
                totals["calories"] += food.get("nf_calories", 0)
                totals["protein"] += food.get("nf_protein", 0)
                totals["carbs"] += food.get("nf_total_carbohydrate", 0)
                totals["fat"] += food.get("nf_total_fat", 0)
                totals["fiber"] += food.get("nf_dietary_fiber", 0)
                totals["sodium"] += food.get("nf_sodium", 0)
                totals["sugar"] += food.get("nf_sugars", 0)
            total_calories = totals["calories"]
            macro_percentages = {}
            if total_calories > 0:
                macro_percentages = {
                    "protein_percent": round((totals["protein"] * 4 / total_calories) * 100, 1),
                    "carbs_percent": round((totals["carbs"] * 4 / total_calories) * 100, 1),
                    "fat_percent": round((totals["fat"] * 9 / total_calories) * 100, 1)
                }
            meal_analysis = {
                "meal_name": meal_name,
                "foods_analyzed": len(food_breakdown),
                "total_nutrition": {
                    "calories": round(totals["calories"], 1),
                    "protein": f"{round(totals['protein'], 1)}g",
                    "carbohydrates": f"{round(totals['carbs'], 1)}g",
                    "fat": f"{round(totals['fat'], 1)}g",
                    "fiber": f"{round(totals['fiber'], 1)}g",
                    "sodium": f"{round(totals['sodium'], 1)}mg",
                    "sugar": f"{round(totals['sugar'], 1)}g"
                },
                "macronutrient_distribution": macro_percentages,
                "food_breakdown": food_breakdown
            }
            return json.dumps(meal_analysis, indent=2)
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error analyzing meal: {str(e)}"

@mcp.tool()
async def calculate_daily_needs(age: int, gender: str, weight_kg: float, height_cm: float, activity_level: str = "moderate") -> str:
    # ... existing code ...
    try:
        if gender.lower() == "male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        multiplier = activity_multipliers.get(activity_level.lower(), 1.55)
        daily_calories = bmr * multiplier
        protein_grams = weight_kg * 0.8
        fat_calories = daily_calories * 0.25
        fat_grams = fat_calories / 9
        carb_calories = daily_calories - (protein_grams * 4) - (fat_grams * 9)
        carb_grams = carb_calories / 4
        fiber_grams = 25 if gender.lower() == "female" else 38
        daily_needs = {
            "personal_info": {
                "age": age,
                "gender": gender,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "activity_level": activity_level,
                "bmr": round(bmr, 1)
            },
            "daily_caloric_needs": round(daily_calories, 0),
            "macronutrient_targets": {
                "protein": f"{round(protein_grams, 1)}g ({round((protein_grams * 4 / daily_calories) * 100, 1)}%)",
                "carbohydrates": f"{round(carb_grams, 1)}g ({round((carb_grams * 4 / daily_calories) * 100, 1)}%)",
                "fat": f"{round(fat_grams, 1)}g ({round((fat_grams * 9 / daily_calories) * 100, 1)}%)",
                "fiber": f"{fiber_grams}g"
            },
            "other_recommendations": {
                "water_liters": round((weight_kg * 35) / 1000, 1),
                "sodium_max_mg": 2300,
                "sugar_max_g": round(daily_calories * 0.1 / 4, 1)
            }
        }
        return json.dumps(daily_needs, indent=2)
    except Exception as e:
        return f"Error calculating daily needs: {str(e)}" 