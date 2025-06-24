import json
import httpx
from datetime import datetime, timedelta
from utils import get_nutritionix_headers, get_wger_headers, NUTRITIONIX_BASE_URL, WGER_BASE_URL
from mcp_server import mcp

@mcp.tool()
async def calculate_exercise_calories(exercise_name: str, duration_min: int = 30, weight_kg: float = 70) -> str:
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
            results = {"query": query, "total_calories_burned": 0, "exercises": []}
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

@mcp.tool()
async def create_fitness_plan(age: int, gender: str, weight_kg: float, height_cm: float, goal: str, activity_level: str = "moderate", workout_days: int = 4, equipment: str = "gym") -> str:
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
        maintenance_calories = bmr * multiplier
        goal_adjustments = {
            "lose_weight": -500,
            "gain_muscle": +300,
            "maintain": 0,
            "athletic_performance": +200
        }
        target_calories = maintenance_calories + goal_adjustments.get(goal, 0)
        if goal == "gain_muscle":
            protein_per_kg = 1.6
        elif goal == "lose_weight":
            protein_per_kg = 1.2
        else:
            protein_per_kg = 1.0
        protein_grams = weight_kg * protein_per_kg
        fat_grams = (target_calories * 0.25) / 9
        carb_grams = (target_calories - (protein_grams * 4) - (fat_grams * 9)) / 4
        equipment_mapping = {
            "gym": "barbell",
            "home": "dumbbell",
            "bodyweight": "bodyweight",
            "minimal": "bodyweight"
        }
        equipment_type = equipment_mapping.get(equipment.lower(), "bodyweight")
        async with httpx.AsyncClient() as client:
            try:
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
                workout_structure = {
                    "chest": [{"name": "Push-ups", "description": "Classic bodyweight chest exercise"}],
                    "back": [{"name": "Pull-ups", "description": "Upper body pulling exercise"}],
                    "legs": [{"name": "Squats", "description": "Fundamental lower body exercise"}],
                    "shoulders": [{"name": "Pike Push-ups", "description": "Bodyweight shoulder exercise"}],
                    "arms": [{"name": "Tricep Dips", "description": "Bodyweight arm exercise"}]
                }
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
async def suggest_pre_post_workout_meals(workout_type: str, duration_min: int = 60, weight_kg: float = 70, goal: str = "maintain") -> str:
    try:
        met_values = {
            "strength": 6.0,
            "cardio": 8.0,
            "mixed": 7.0,
            "hiit": 10.0
        }
        met = met_values.get(workout_type.lower(), 7.0)
        calories_burned = (met * weight_kg * (duration_min / 60))
        if goal == "lose_weight":
            pre_workout_calories = 100
            post_workout_calories = 150
        elif goal == "gain_muscle":
            pre_workout_calories = 200
            post_workout_calories = 300
        elif goal == "endurance":
            pre_workout_calories = 250
            post_workout_calories = 200
        else:
            pre_workout_calories = 150
            post_workout_calories = 200
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
async def track_weekly_progress(current_weight: float, target_weight: float, weekly_workouts_completed: int, goal: str = "lose_weight") -> str:
    try:
        weight_difference = current_weight - target_weight
        if goal == "lose_weight":
            ideal_weekly_loss = 0.5
            progress_status = "On track" if abs(weight_difference) > 0 else "Target reached"
            weeks_to_goal = max(1, round(weight_difference / ideal_weekly_loss, 0)) if weight_difference > 0 else 0
        elif goal == "gain_muscle":
            ideal_weekly_gain = 0.25
            progress_status = "On track" if weight_difference < 0 else "Target reached"
            weeks_to_goal = max(1, round(abs(weight_difference) / ideal_weekly_gain, 0)) if weight_difference < 0 else 0
        else:
            progress_status = "Maintaining" if abs(weight_difference) <= 1 else "Adjustment needed"
            weeks_to_goal = 0
        recommended_workouts = 4
        workout_progress = (weekly_workouts_completed / recommended_workouts) * 100
        if workout_progress >= 100:
            workout_status = "Excellent - exceeded target"
        elif workout_progress >= 75:
            workout_status = "Good - on track"
        elif workout_progress >= 50:
            workout_status = "Fair - room for improvement"
        else:
            workout_status = "Poor - need to increase frequency"
        recommendations = []
        if weekly_workouts_completed < recommended_workouts:
            recommendations.append("Increase workout frequency to reach your goals faster")
        if goal == "lose_weight" and weight_difference > 0:
            recommendations.append("Consider reducing daily calories by 100-200 or increasing cardio")
        elif goal == "gain_muscle" and weight_difference < -1:
            recommendations.append("You may be gaining weight too quickly - ensure it's muscle, not fat")
        if workout_progress < 75:
            recommendations.append("Try to maintain consistency with your workout schedule")
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