"""
Complete Fitness & Nutrition MCP Server

A Model Context Protocol server that integrates:
- Nutritionix API for food and nutrition data
- WGER API for workout and exercise data

Requirements:
- Nutritionix API credentials (APP_ID and APP_KEY)
- httpx for async HTTP requests
- WGER API is free and requires no authentication

Environment Variables:
- NUTRITIONIX_APP_ID: Your Nutritionix application ID
- NUTRITIONIX_APP_KEY: Your Nutritionix application key
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from mcp.server.fastmcp import FastMCP


# Initialize the MCP server
mcp = FastMCP(
    "Fitness & Nutrition API",
    dependencies=["httpx"]
)

# API configurations
NUTRITIONIX_BASE_URL = "https://trackapi.nutritionix.com/v2"
WGER_BASE_URL = "https://wger.de/api/v2"

NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

if not NUTRITIONIX_APP_ID or not NUTRITIONIX_APP_KEY:
    raise ValueError(
        "Missing Nutritionix API credentials. Please set NUTRITIONIX_APP_ID and NUTRITIONIX_APP_KEY environment variables."
    )


def get_nutritionix_headers() -> Dict[str, str]:
    """Get headers for Nutritionix API requests."""
    return {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_APP_KEY,
        "Content-Type": "application/json"
    }


def get_wger_headers() -> Dict[str, str]:
    """Get headers for WGER API requests."""
    return {
        "Accept": "application/json",
        "User-Agent": "Fitness-Nutrition-MCP-Server/1.0"
    }


# =============================================================================
# NUTRITIONIX API ENDPOINTS
# =============================================================================

@mcp.tool()
async def search_foods(query: str, limit: int = 10) -> str:
    """
    Search for foods using the Nutritionix database.
    
    Args:
        query: The food search term (e.g., "apple", "chicken breast")
        limit: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        JSON string containing search results with basic food information
    """
    if limit > 50:
        limit = 50
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NUTRITIONIX_BASE_URL}/search/instant",
                headers=get_nutritionix_headers(),
                params={
                    "query": query,
                    "detailed": True
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            results = {
                "query": query,
                "common_foods": [],
                "branded_foods": []
            }
            
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
    """
    Get detailed nutritional information for a specific food.
    
    Args:
        food_name: Name of the food (e.g., "1 large apple", "100g chicken breast")
        quantity: Amount of the food (default: 1.0)
        unit: Unit of measurement (default: "serving")
    
    Returns:
        JSON string containing detailed nutritional information
    """
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
    """
    Compare nutritional information between two foods side by side.
    
    Args:
        food1: First food to compare
        food2: Second food to compare
        quantity: Amount for both foods (default: 1.0)
        unit: Unit of measurement for both foods (default: "serving")
    
    Returns:
        JSON string containing side-by-side nutritional comparison
    """
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
    """
    Analyze the total nutritional content of a complete meal.
    
    Args:
        foods_list: List of foods in the meal (e.g., ["1 cup rice", "100g chicken", "1 medium apple"])
        meal_name: Name for the meal (default: "Custom Meal")
    
    Returns:
        JSON string containing total nutritional analysis of the meal
    """
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
            
            totals = {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0,
                "fiber": 0,
                "sodium": 0,
                "sugar": 0
            }
            
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
async def calculate_daily_needs(age: int, gender: str, weight_kg: float, height_cm: float, 
                               activity_level: str = "moderate") -> str:
    """
    Calculate daily caloric and nutritional needs based on personal characteristics.
    
    Args:
        age: Age in years
        gender: "male" or "female"
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        activity_level: "sedentary", "light", "moderate", "active", or "very_active"
    
    Returns:
        JSON string containing calculated daily nutritional needs
    """
    try:
        # Calculate BMR using Mifflin-St Jeor Equation
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
        
        # Calculate macronutrient needs
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


# =============================================================================
# WGER API ENDPOINTS
# =============================================================================

@mcp.tool()
async def search_exercises(query: str, limit: int = 20) -> str:
    """
    Search for exercises in the WGER database.
    
    Args:
        query: Exercise search term (e.g., "squat", "bench press", "cardio")
        limit: Maximum number of results to return (default: 20)
    
    Returns:
        JSON string containing exercise search results
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{WGER_BASE_URL}/exercise/",
                headers=get_wger_headers(),
                params={
                    "search": query,
                    "limit": limit,
                    "language": 2  # English
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            exercises = []
            for exercise in data.get("results", []):
                exercise_info = {
                    "id": exercise.get("id"),
                    "name": exercise.get("name"),
                    "description": exercise.get("description", "").replace("<p>", "").replace("</p>", ""),
                    "category": exercise.get("category"),
                    "muscles": exercise.get("muscles", []),
                    "muscles_secondary": exercise.get("muscles_secondary", []),
                    "equipment": exercise.get("equipment", [])
                }
                exercises.append(exercise_info)
            
            results = {
                "query": query,
                "total_found": data.get("count", 0),
                "exercises": exercises
            }
            
            return json.dumps(results, indent=2)
            
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching exercises: {str(e)}"


@mcp.tool()
async def get_exercises_by_muscle(muscle_group: str, limit: int = 15) -> str:
    """
    Get exercises targeting specific muscle groups.
    
    Args:
        muscle_group: Target muscle group (e.g., "chest", "legs", "back", "shoulders", "arms")
        limit: Maximum number of exercises to return (default: 15)
    
    Returns:
        JSON string containing exercises for the specified muscle group
    """
    # Muscle group mapping to WGER muscle IDs
    muscle_mapping = {
        "chest": [4],  # Chest
        "back": [12, 13],  # Lats, Rhomboids
        "shoulders": [2, 3],  # Anterior deltoid, Posterior deltoid
        "arms": [1, 5, 8],  # Biceps, Triceps, Forearms
        "legs": [10, 11, 7, 9],  # Quadriceps, Hamstrings, Glutes, Calves
        "abs": [14, 6],  # Rectus abdominis, Obliques
        "core": [14, 6]  # Same as abs
    }
    
    muscle_ids = muscle_mapping.get(muscle_group.lower(), [])
    
    if not muscle_ids:
        available_groups = ", ".join(muscle_mapping.keys())
        return f"Invalid muscle group. Available groups: {available_groups}"
    
    async with httpx.AsyncClient() as client:
        try:
            exercises = []
            
            for muscle_id in muscle_ids:
                response = await client.get(
                    f"{WGER_BASE_URL}/exercise/",
                    headers=get_wger_headers(),
                    params={
                        "muscles": muscle_id,
                        "limit": limit // len(muscle_ids),
                        "language": 2
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                for exercise in data.get("results", []):
                    exercise_info = {
                        "id": exercise.get("id"),
                        "name": exercise.get("name"),
                        "description": exercise.get("description", "").replace("<p>", "").replace("</p>", ""),
                        "primary_muscles": exercise.get("muscles", []),
                        "secondary_muscles": exercise.get("muscles_secondary", []),
                        "equipment": exercise.get("equipment", [])
                    }
                    exercises.append(exercise_info)
            
            results = {
                "muscle_group": muscle_group,
                "total_exercises": len(exercises),
                "exercises": exercises[:limit]
            }
            
            return json.dumps(results, indent=2)
            
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting exercises by muscle: {str(e)}"


@mcp.tool()
async def get_equipment_exercises(equipment_name: str, limit: int = 15) -> str:
    """
    Get exercises that can be performed with specific equipment.
    
    Args:
        equipment_name: Equipment type (e.g., "dumbbell", "barbell", "bodyweight", "machine")
        limit: Maximum number of exercises to return (default: 15)
    
    Returns:
        JSON string containing exercises for the specified equipment
    """
    async with httpx.AsyncClient() as client:
        try:
            # First get equipment list to find the ID
            equipment_response = await client.get(
                f"{WGER_BASE_URL}/equipment/",
                headers=get_wger_headers(),
                params={"limit": 50}
            )
            equipment_response.raise_for_status()
            
            equipment_data = equipment_response.json()
            equipment_id = None
            
            # Search for equipment by name
            for equipment in equipment_data.get("results", []):
                if equipment_name.lower() in equipment.get("name", "").lower():
                    equipment_id = equipment.get("id")
                    break
            
            if not equipment_id:
                # Try some common mappings
                equipment_mapping = {
                    "dumbbell": 1,
                    "barbell": 2,
                    "bodyweight": 7,
                    "machine": 3,
                    "cable": 4,
                    "kettlebell": 9
                }
                equipment_id = equipment_mapping.get(equipment_name.lower())
            
            if not equipment_id:
                return f"Equipment '{equipment_name}' not found. Try: dumbbell, barbell, bodyweight, machine, cable, kettlebell"
            
            # Get exercises for this equipment
            response = await client.get(
                f"{WGER_BASE_URL}/exercise/",
                headers=get_wger_headers(),
                params={
                    "equipment": equipment_id,
                    "limit": limit,
                    "language": 2
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            exercises = []
            for exercise in data.get("results", []):
                exercise_info = {
                    "id": exercise.get("id"),
                    "name": exercise.get("name"),
                    "description": exercise.get("description", "").replace("<p>", "").replace("</p>", ""),
                    "primary_muscles": exercise.get("muscles", []),
                    "secondary_muscles": exercise.get("muscles_secondary", []),
                    "equipment": exercise.get("equipment", [])
                }
                exercises.append(exercise_info)
            
            results = {
                "equipment": equipment_name,
                "total_exercises": len(exercises),
                "exercises": exercises
            }
            
            return json.dumps(results, indent=2)
            
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting equipment exercises: {str(e)}"


@mcp.tool()
async def get_workout_templates(difficulty: str = "intermediate") -> str:
    """
    Get pre-made workout templates from WGER.
    
    Args:
        difficulty: Workout difficulty ("beginner", "intermediate", "advanced")
    
    Returns:
        JSON string containing workout templates
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{WGER_BASE_URL}/workout/",
                headers=get_wger_headers(),
                params={"limit": 20}
            )
            response.raise_for_status()
            
            data = response.json()
            
            workouts = []
            for workout in data.get("results", []):
                # Get workout details
                workout_info = {
                    "id": workout.get("id"),
                    "name": workout.get("name", f"Workout {workout.get('id')}"),
                    "creation_date": workout.get("creation_date"),
                    "description": workout.get("comment", "")
                }
                workouts.append(workout_info)
            
            results = {
                "difficulty": difficulty,
                "available_workouts": len(workouts),
                "workouts": workouts
            }
            
            return json.dumps(results, indent=2)
            
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting workout templates: {str(e)}"


@mcp.tool()
async def calculate_exercise_calories(exercise_name: str, duration_min: int = 30, weight_kg: float = 70) -> str:
    """
    Calculate calories burned for exercises using Nutritionix exercise API.
    
    Args:
        exercise_name: Name of the exercise (e.g., "running", "cycling", "weight lifting")
        duration_min: Duration in minutes (default: 30)
        weight_kg: Body weight in kilograms (default: 70)
    
    Returns:
        JSON string containing exercise and calories burned information
    """
    if duration_min != 30:
        query = f"{duration_min} minutes {exercise_name}"
    else:
        query = exercise_name
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {"query": query}
            if weight_kg:
                payload["weight_kg"] = weight_kg
            
            response = await client.post(
                f"{NUTRITIONIX_BASE_URL}/natural/exercise",
                headers=get_nutritionix_headers(),
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "exercises" not in data or not data["exercises"]:
                return f"No exercise information found for: {query}"
            
            results = {
                "query": query,
                "total_calories_burned": 0,
                "exercises": []
            }
            
            for exercise_data in data["exercises"]:
                exercise_info = {
                    "name": exercise_data.get("name"),
                    "duration_min": exercise_data.get("duration_min"),
                    "met": exercise_data.get("met"),
                    "nf_calories": exercise_data.get("nf_calories"),
                    "user_weight_kg": exercise_data.get("user_weight_kg")
                }
                results["exercises"].append(exercise_info)
                results["total_calories_burned"] += exercise_data.get("nf_calories", 0)
            
            return json.dumps(results, indent=2)
            
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error calculating exercise calories: {str(e)}"


# =============================================================================
# COMBINED FUNCTIONALITY ENDPOINTS
# =============================================================================

@mcp.tool()
async def create_fitness_plan(age: int, gender: str, weight_kg: float, height_cm: float, 
                             goal: str, activity_level: str = "moderate", 
                             workout_days: int = 4, equipment: str = "gym") -> str:
    """
    Create a comprehensive fitness plan combining nutrition and workout recommendations.
    
    Args:
        age: Age in years
        gender: "male" or "female"
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        goal: Fitness goal ("lose_weight", "gain_muscle", "maintain", "athletic_performance")
        activity_level: Current activity level ("sedentary", "light", "moderate", "active", "very_active")
        workout_days: Number of workout days per week (default: 4)
        equipment: Available equipment ("gym", "home", "bodyweight", "minimal")
    
    Returns:
        JSON string containing comprehensive fitness plan
    """
    try:
        # Calculate daily nutritional needs
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
        maintenance_calories = bmr * multiplier
        
        # Adjust calories based on goal
        goal_adjustments = {
            "lose_weight": -500,  # 500 calorie deficit
            "gain_muscle": +300,  # 300 calorie surplus
            "maintain": 0,
            "athletic_performance": +200
        }
        
        target_calories = maintenance_calories + goal_adjustments.get(goal, 0)
        
        # Calculate macronutrients based on goal
        if goal == "gain_muscle":
            protein_per_kg = 1.6  # Higher protein for muscle gain
        elif goal == "lose_weight":
            protein_per_kg = 1.2  # Moderate protein for weight loss
        else:
            protein_per_kg = 1.0
        
        protein_grams = weight_kg * protein_per_kg
        fat_grams = (target_calories * 0.25) / 9  # 25% of calories from fat
        carb_grams = (target_calories - (protein_grams * 4) - (fat_grams * 9)) / 4
        
        # Create workout recommendations based on equipment
        equipment_mapping = {
            "gym": "barbell",
            "home": "dumbbell", 
            "bodyweight": "bodyweight",
            "minimal": "bodyweight"
        }
        
        equipment_type = equipment_mapping.get(equipment.lower(), "bodyweight")
        
        # Get exercise recommendations
        async with httpx.AsyncClient() as client:
            try:
                # Get exercises for different muscle groups
                muscle_groups = ["chest", "back", "legs", "shoulders", "arms"]
                workout_structure = {}
                
                for muscle in muscle_groups:
                    muscle_ids = {
                        "chest": [4],
                        "back": [12, 13],
                        "legs": [10, 11, 7, 9],
                        "shoulders": [2, 3],
                        "arms": [1, 5, 8]
                    }.get(muscle, [])
                    
                    if muscle_ids:
                        response = await client.get(
                            f"{WGER_BASE_URL}/exercise/",
                            headers=get_wger_headers(),
                            params={
                                "muscles": muscle_ids[0],
                                "limit": 3,
                                "language": 2
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            exercises = []
                            for ex in data.get("results", [])[:3]:
                                exercises.append({
                                    "name": ex.get("name"),
                                    "description": ex.get("description", "").replace("<p>", "").replace("</p>", "")[:100] + "..."
                                })
                            workout_structure[muscle] = exercises
                
            except:
                # Fallback workout structure
                workout_structure = {
                    "chest": [{"name": "Push-ups", "description": "Classic bodyweight chest exercise"}],
                    "back": [{"name": "Pull-ups", "description": "Upper body pulling exercise"}],
                    "legs": [{"name": "Squats", "description": "Fundamental lower body exercise"}],
                    "shoulders": [{"name": "Pike Push-ups", "description": "Bodyweight shoulder exercise"}],
                    "arms": [{"name": "Tricep Dips", "description": "Bodyweight arm exercise"}]
                }
        
        # Create sample meal plan
        sample_meals = {
            "breakfast": [
                "3 eggs scrambled",
                "2 slices whole wheat toast", 
                "1 medium banana",
                "1 cup coffee"
            ],
            "lunch": [
                f"{round(protein_grams/4, 0)}g grilled chicken breast",
                "1 cup brown rice",
                "1 cup steamed vegetables",
                "1 tbsp olive oil"
            ],
            "dinner": [
                f"{round(protein_grams/4, 0)}g lean protein (fish/meat)",
                "1 cup quinoa",
                "Mixed green salad",
                "1 tbsp dressing"
            ],
            "snacks": [
                "1 cup greek yogurt",
                "1/4 cup nuts",
                "1 apple with 2 tbsp peanut butter"
            ]
        }
        
        # Create weekly workout split
        if workout_days >= 4:
            workout_split = {
                "day_1": {"focus": "Chest & Triceps", "exercises": workout_structure.get("chest", []) + workout_structure.get("arms", [])[:2]},
                "day_2": {"focus": "Back & Biceps", "exercises": workout_structure.get("back", []) + workout_structure.get("arms", [])[1:]},
                "day_3": {"focus": "Legs", "exercises": workout_structure.get("legs", [])},
                "day_4": {"focus": "Shoulders & Core", "exercises": workout_structure.get("shoulders", [])}
            }
            if workout_days >= 5:
                workout_split["day_5"] = {"focus": "Full Body / Cardio", "exercises": [{"name": "30min cardio", "description": "Choose your preferred cardio activity"}]}
        else:
            workout_split = {
                "day_1": {"focus": "Upper Body", "exercises": workout_structure.get("chest", []) + workout_structure.get("back", [])},
                "day_2": {"focus": "Lower Body", "exercises": workout_structure.get("legs", [])},
                "day_3": {"focus": "Full Body", "exercises": workout_structure.get("shoulders", []) + workout_structure.get("arms", [])}
            }
        
        fitness_plan = {
            "personal_profile": {
                "age": age,
                "gender": gender,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "bmr": round(bmr, 0),
                "goal": goal,
                "activity_level": activity_level
            },
            "nutrition_plan": {
                "daily_calories": {
                    "maintenance": round(maintenance_calories, 0),
                    "target": round(target_calories, 0),
                    "adjustment": goal_adjustments.get(goal, 0)
                },
                "macronutrient_targets": {
                    "protein": f"{round(protein_grams, 1)}g ({round((protein_grams * 4 / target_calories) * 100, 1)}%)",
                    "carbohydrates": f"{round(carb_grams, 1)}g ({round((carb_grams * 4 / target_calories) * 100, 1)}%)",
                    "fat": f"{round(fat_grams, 1)}g ({round((fat_grams * 9 / target_calories) * 100, 1)}%)"
                },
                "sample_meal_plan": sample_meals,
                "hydration": f"{round((weight_kg * 35) / 1000, 1)} liters water daily"
            },
            "workout_plan": {
                "frequency": f"{workout_days} days per week",
                "equipment": equipment,
                "weekly_split": workout_split,
                "general_guidelines": [
                    "Warm up 5-10 minutes before each workout",
                    "Cool down and stretch after each workout",
                    "Rest 48-72 hours between training the same muscle group",
                    "Progressive overload: gradually increase weight/reps/sets",
                    "Listen to your body and rest when needed"
                ]
            },
            "progress_tracking": {
                "weekly_goals": {
                    "weight_change": "0.5-1kg per week" if goal == "lose_weight" else "0.25-0.5kg per week" if goal == "gain_muscle" else "maintain current weight",
                    "strength": "Increase weights by 2.5-5% when you can complete all sets with good form",
                    "measurements": "Track waist, chest, arms, thighs weekly"
                },
                "recommended_metrics": [
                    "Daily weight (same time each day)",
                    "Weekly body measurements",
                    "Workout performance (weights, reps, sets)",
                    "Energy levels (1-10 scale)",
                    "Sleep quality (hours and quality)"
                ]
            }
        }
        
        return json.dumps(fitness_plan, indent=2)
        
    except Exception as e:
        return f"Error creating fitness plan: {str(e)}"


@mcp.tool()
async def suggest_pre_post_workout_meals(workout_type: str, duration_min: int = 60, 
                                       weight_kg: float = 70, goal: str = "maintain") -> str:
    """
    Suggest optimal pre and post-workout meals based on workout type and goals.
    
    Args:
        workout_type: Type of workout ("strength", "cardio", "mixed", "hiit")
        duration_min: Workout duration in minutes (default: 60)
        weight_kg: Body weight in kilograms (default: 70)
        goal: Fitness goal ("lose_weight", "gain_muscle", "maintain", "endurance")
    
    Returns:
        JSON string containing pre and post-workout meal recommendations
    """
    try:
        # Calculate approximate calories burned based on workout type
        met_values = {
            "strength": 6.0,
            "cardio": 8.0,
            "mixed": 7.0,
            "hiit": 10.0
        }
        
        met = met_values.get(workout_type.lower(), 7.0)
        calories_burned = (met * weight_kg * (duration_min / 60))
        
        # Adjust recommendations based on goal
        if goal == "lose_weight":
            pre_workout_calories = 100
            post_workout_calories = 150
        elif goal == "gain_muscle":
            pre_workout_calories = 200
            post_workout_calories = 300
        elif goal == "endurance":
            pre_workout_calories = 250
            post_workout_calories = 200
        else:  # maintain
            pre_workout_calories = 150
            post_workout_calories = 200
        
        # Pre-workout meal suggestions (1-2 hours before)
        pre_workout_options = {
            "strength": [
                {
                    "meal": "Banana with almond butter",
                    "foods": ["1 medium banana", "2 tbsp almond butter"],
                    "timing": "30-60 minutes before",
                    "benefits": "Quick carbs for energy, healthy fats for sustained energy"
                },
                {
                    "meal": "Oatmeal with berries",
                    "foods": ["1/2 cup oats", "1/2 cup berries", "1 tbsp honey"],
                    "timing": "1-2 hours before",
                    "benefits": "Complex carbs for sustained energy"
                }
            ],
            "cardio": [
                {
                    "meal": "Toast with jam",
                    "foods": ["1 slice whole wheat bread", "1 tbsp jam"],
                    "timing": "30-45 minutes before",
                    "benefits": "Quick carbs for immediate energy"
                },
                {
                    "meal": "Greek yogurt with fruit",
                    "foods": ["1 cup greek yogurt", "1/2 cup berries"],
                    "timing": "1-2 hours before",
                    "benefits": "Protein + carbs for energy and muscle protection"
                }
            ]
        }
        
        # Post-workout meal suggestions (within 30-60 minutes)
        post_workout_options = {
            "strength": [
                {
                    "meal": "Protein shake with banana",
                    "foods": ["1 scoop whey protein", "1 medium banana", "1 cup milk"],
                    "timing": "Within 30 minutes",
                    "benefits": "Fast protein for muscle recovery, carbs to replenish glycogen"
                },
                {
                    "meal": "Chicken and rice bowl",
                    "foods": ["100g grilled chicken", "1/2 cup cooked rice", "vegetables"],
                    "timing": "Within 60 minutes",
                    "benefits": "Complete protein and carbs for recovery"
                }
            ],
            "cardio": [
                {
                    "meal": "Chocolate milk",
                    "foods": ["1 cup low-fat chocolate milk"],
                    "timing": "Within 30 minutes",
                    "benefits": "3:1 carb to protein ratio ideal for recovery"
                },
                {
                    "meal": "Tuna sandwich",
                    "foods": ["2 slices whole wheat bread", "1 can tuna", "vegetables"],
                    "timing": "Within 60 minutes",
                    "benefits": "Lean protein and complex carbs"
                }
            ]
        }
        
        # Get specific recommendations for workout type
        pre_options = pre_workout_options.get(workout_type.lower(), pre_workout_options["strength"])
        post_options = post_workout_options.get(workout_type.lower(), post_workout_options["strength"])
        
        recommendations = {
            "workout_info": {
                "type": workout_type,
                "duration_minutes": duration_min,
                "estimated_calories_burned": round(calories_burned, 0),
                "weight_kg": weight_kg,
                "goal": goal
            },
            "pre_workout": {
                "target_calories": pre_workout_calories,
                "general_guidelines": [
                    "Eat 1-3 hours before workout",
                    "Focus on carbohydrates for energy",
                    "Include some protein if eating 2+ hours before",
                    "Avoid high fat and fiber foods close to workout",
                    "Stay hydrated"
                ],
                "meal_options": pre_options
            },
            "post_workout": {
                "target_calories": post_workout_calories,
                "general_guidelines": [
                    "Eat within 30-60 minutes after workout",
                    "Include both protein and carbohydrates",
                    "Aim for 3:1 or 4:1 carb to protein ratio",
                    "Rehydrate with water or electrolyte drinks",
                    "Include anti-inflammatory foods"
                ],
                "meal_options": post_options
            },
            "hydration_strategy": {
                "before": "500ml water 2-3 hours before workout",
                "during": f"{round(150 * (duration_min / 60), 0)}ml every 15-20 minutes during workout",
                "after": f"{round(calories_burned * 1.5, 0)}ml to replace fluid losses"
            }
        }
        
        return json.dumps(recommendations, indent=2)
        
    except Exception as e:
        return f"Error suggesting workout meals: {str(e)}"


@mcp.tool()
async def track_weekly_progress(current_weight: float, target_weight: float, 
                               weekly_workouts_completed: int, goal: str = "lose_weight") -> str:
    """
    Track and analyze weekly fitness progress with recommendations.
    
    Args:
        current_weight: Current weight in kg
        target_weight: Target weight in kg
        weekly_workouts_completed: Number of workouts completed this week
        goal: Fitness goal ("lose_weight", "gain_muscle", "maintain")
    
    Returns:
        JSON string containing progress analysis and recommendations
    """
    try:
        weight_difference = current_weight - target_weight
        
        # Determine if progress is on track
        if goal == "lose_weight":
            ideal_weekly_loss = 0.5  # kg per week
            progress_status = "On track" if abs(weight_difference) > 0 else "Target reached"
            weeks_to_goal = max(1, round(weight_difference / ideal_weekly_loss, 0)) if weight_difference > 0 else 0
        elif goal == "gain_muscle":
            ideal_weekly_gain = 0.25  # kg per week
            progress_status = "On track" if weight_difference < 0 else "Target reached"
            weeks_to_goal = max(1, round(abs(weight_difference) / ideal_weekly_gain, 0)) if weight_difference < 0 else 0
        else:  # maintain
            progress_status = "Maintaining" if abs(weight_difference) <= 1 else "Adjustment needed"
            weeks_to_goal = 0
        
        # Workout progress analysis
        recommended_workouts = 4  # per week
        workout_progress = (weekly_workouts_completed / recommended_workouts) * 100
        
        if workout_progress >= 100:
            workout_status = "Excellent - exceeded target"
        elif workout_progress >= 75:
            workout_status = "Good - on track"
        elif workout_progress >= 50:
            workout_status = "Fair - room for improvement"
        else:
            workout_status = "Poor - need to increase frequency"
        
        # Generate recommendations
        recommendations = []
        
        if weekly_workouts_completed < recommended_workouts:
            recommendations.append("Increase workout frequency to reach your goals faster")
        
        if goal == "lose_weight" and weight_difference > 0:
            recommendations.append("Consider reducing daily calories by 100-200 or increasing cardio")
        elif goal == "gain_muscle" and weight_difference < -1:
            recommendations.append("You may be gaining weight too quickly - ensure it's muscle, not fat")
        
        if workout_progress < 75:
            recommendations.append("Try to maintain consistency with your workout schedule")
        
        # Create progress summary
        progress_summary = {
            "current_status": {
                "current_weight_kg": current_weight,
                "target_weight_kg": target_weight,
                "weight_difference_kg": round(weight_difference, 1),
                "goal": goal,
                "progress_status": progress_status
            },
            "weekly_performance": {
                "workouts_completed": weekly_workouts_completed,
                "workouts_recommended": recommended_workouts,
                "completion_percentage": round(workout_progress, 1),
                "workout_status": workout_status
            },
            "projections": {
                "estimated_weeks_to_goal": int(weeks_to_goal) if weeks_to_goal > 0 else 0,
                "target_date": (datetime.now() + timedelta(weeks=weeks_to_goal)).strftime("%Y-%m-%d") if weeks_to_goal > 0 else "Target achieved"
            },
            "recommendations": recommendations,
            "next_week_targets": {
                "weight_target": current_weight - ideal_weekly_loss if goal == "lose_weight" else current_weight + ideal_weekly_gain if goal == "gain_muscle" else current_weight,
                "workout_target": recommended_workouts,
                "focus_areas": [
                    "Maintain consistent workout schedule",
                    "Track food intake accurately",
                    "Get adequate sleep (7-9 hours)",
                    "Stay hydrated",
                    "Monitor energy levels"
                ]
            }
        }
        
        return json.dumps(progress_summary, indent=2)
        
    except Exception as e:
        return f"Error tracking progress: {str(e)}"


# =============================================================================
# RESOURCES
# =============================================================================

@mcp.resource("fitness://status")
def get_api_status() -> str:
    """Get the current status and configuration of both APIs."""
    status = {
        "service": "Complete Fitness & Nutrition API",
        "apis_integrated": [
            {
                "name": "Nutritionix",
                "base_url": NUTRITIONIX_BASE_URL,
                "status": "connected" if NUTRITIONIX_APP_ID and NUTRITIONIX_APP_KEY else "disconnected",
                "features": ["Food search", "Nutrition analysis", "Meal planning", "Exercise calories"]
            },
            {
                "name": "WGER",
                "base_url": WGER_BASE_URL,
                "status": "connected",
                "features": ["Exercise database", "Workout templates", "Muscle group targeting", "Equipment-based exercises"]
            }
        ],
        "combined_features": [
            "Complete fitness plans",
            "Pre/post workout nutrition",
            "Progress tracking",
            "Goal-based recommendations"
        ]
    }
    return json.dumps(status, indent=2)


@mcp.resource("fitness://help")
def get_help() -> str:
    """Get comprehensive help for the fitness and nutrition server."""
    help_text = """
# Complete Fitness & Nutrition MCP Server Help

## 🍎 NUTRITION TOOLS (Nutritionix API):

### Core Nutrition Functions:
- **search_foods(query, limit=10)** - Search food database
- **get_food_nutrients(food_name, quantity=1.0, unit="serving")** - Get detailed nutrition
- **compare_foods(food1, food2, quantity=1.0, unit="serving")** - Compare two foods
- **analyze_meal(foods_list, meal_name)** - Analyze complete meals
- **calculate_daily_needs(age, gender, weight_kg, height_cm, activity_level)** - Calculate daily nutritional needs

## 💪 WORKOUT TOOLS (WGER API):

### Exercise & Workout Functions:
- **search_exercises(query, limit=20)** - Search exercise database
- **get_exercises_by_muscle(muscle_group, limit=15)** - Get exercises by muscle group
  - Available muscle groups: chest, back, shoulders, arms, legs, abs, core
- **get_equipment_exercises(equipment_name, limit=15)** - Get exercises by equipment
  - Available equipment: dumbbell, barbell, bodyweight, machine, cable, kettlebell
- **get_workout_templates(difficulty="intermediate")** - Get pre-made workout templates
- **calculate_exercise_calories(exercise_name, duration_min=30, weight_kg=70)** - Calculate calories burned

## 🎯 COMBINED TOOLS (Both APIs):

### Complete Fitness Solutions:
- **create_fitness_plan(age, gender, weight_kg, height_cm, goal, activity_level, workout_days, equipment)**
  - Goals: "lose_weight", "gain_muscle", "maintain", "athletic_performance"
  - Equipment: "gym", "home", "bodyweight", "minimal"
  
- **suggest_pre_post_workout_meals(workout_type, duration_min=60, weight_kg=70, goal="maintain")**
  - Workout types: "strength", "cardio", "mixed", "hiit"
  
- **track_weekly_progress(current_weight, target_weight, weekly_workouts_completed, goal)**

## 📊 USAGE EXAMPLES:

### Complete Fitness Plan:
```
create_fitness_plan(25, "male", 80, 180, "lose_weight", "moderate", 4, "gym")
```

### Workout + Nutrition:
```
# Get chest exercises
get_exercises_by_muscle("chest", 5)

# Plan pre-workout meal
suggest_pre_post_workout_meals("strength", 90, 75, "gain_muscle")

# Analyze post-workout meal
analyze_meal(["1 scoop whey protein", "1 banana", "1 cup milk"], "Post-Workout")
```

### Progress Tracking:
```
track_weekly_progress(78.5, 75, 3, "lose_weight")
```

## 🎯 GOAL-BASED WORKFLOWS:

### Weight Loss:
1. `calculate_daily_needs()` - Get calorie targets
2. `create_fitness_plan()` with goal="lose_weight"
3. `get_exercises_by_muscle()` for each muscle group
4. `suggest_pre_post_workout_meals()` for workout nutrition
5. `track_weekly_progress()` to monitor results

### Muscle Gain:
1. `create_fitness_plan()` with goal="gain_muscle"
2. `get_equipment_exercises()` for available equipment
3. `analyze_meal()` to ensure adequate protein
4. `suggest_pre_post_workout_meals()` for optimal timing

### Maintenance:
1. `calculate_daily_needs()` for maintenance calories
2. `get_workout_templates()` for variety
3. `compare_foods()` for healthy swaps
4. `track_weekly_progress()` to stay on track

## 🏃‍♂️ MUSCLE GROUPS:
- **chest** - Pectorals, chest muscles
- **back** - Lats, rhomboids, rear delts
- **shoulders** - Front and rear deltoids
- **arms** - Biceps, triceps, forearms
- **legs** - Quads, hamstrings, glutes, calves
- **abs/core** - Abdominals, obliques

## 🏋️ EQUIPMENT TYPES:
- **gym** - Full gym access
- **home** - Home gym with dumbbells
- **bodyweight** - No equipment needed
- **minimal** - Basic equipment only

## 🎯 FITNESS GOALS:
- **lose_weight** - Fat loss focus
- **gain_muscle** - Muscle building focus
- **maintain** - Maintain current physique
- **athletic_performance** - Performance enhancement

## Setup:
1. Get Nutritionix API credentials from https://www.nutritionix.com/business/api
2. Set environment variables: NUTRITIONIX_APP_ID and NUTRITIONIX_APP_KEY
3. WGER API requires no authentication (free to use)
4. Install: mcp install fitness_nutrition_server.py
"""
    return help_text


if __name__ == "__main__":
    # Run the server
    mcp.run()