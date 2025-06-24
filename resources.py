import json
from mcp_server import mcp
from utils import NUTRITIONIX_BASE_URL, WGER_BASE_URL, NUTRITIONIX_APP_ID, NUTRITIONIX_APP_KEY

@mcp.resource("fitness://status")
def get_api_status() -> str:
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
    help_text = """
# Complete Fitness & Nutrition MCP Server Help

## 🍎 NUTRITION TOOLS (Nutritionix API):

### Core Nutrition Functions:
- **search_foods(query, limit=10)** - Search food database
- **get_food_nutrients(food_name, quantity=1.0, unit=\"serving\")** - Get detailed nutrition
- **compare_foods(food1, food2, quantity=1.0, unit=\"serving\")** - Compare two foods
- **analyze_meal(foods_list, meal_name)** - Analyze complete meals
- **calculate_daily_needs(age, gender, weight_kg, height_cm, activity_level)** - Calculate daily nutritional needs

## 💪 WORKOUT TOOLS (WGER API):

### Exercise & Workout Functions:
- **search_exercises(query, limit=20)** - Search exercise database
- **get_exercises_by_muscle(muscle_group, limit=15)** - Get exercises by muscle group
  - Available muscle groups: chest, back, shoulders, arms, legs, abs, core
- **get_equipment_exercises(equipment_name, limit=15)** - Get exercises by equipment
  - Available equipment: dumbbell, barbell, bodyweight, machine, cable, kettlebell
- **get_workout_templates(difficulty=\"intermediate\")** - Get pre-made workout templates
- **calculate_exercise_calories(exercise_name, duration_min=30, weight_kg=70)** - Calculate calories burned

## 🎯 COMBINED TOOLS (Both APIs):

### Complete Fitness Solutions:
- **create_fitness_plan(age, gender, weight_kg, height_cm, goal, activity_level, workout_days, equipment)**
  - Goals: \"lose_weight\", \"gain_muscle\", \"maintain\", \"athletic_performance\"
  - Equipment: \"gym\", \"home\", \"bodyweight\", \"minimal\"
  
- **suggest_pre_post_workout_meals(workout_type, duration_min=60, weight_kg=70, goal=\"maintain\")**
  - Workout types: \"strength\", \"cardio\", \"mixed\", \"hiit\"
  
- **track_weekly_progress(current_weight, target_weight, weekly_workouts_completed, goal)**

## 📊 USAGE EXAMPLES:

### Complete Fitness Plan:
```
create_fitness_plan(25, \"male\", 80, 180, \"lose_weight\", \"moderate\", 4, \"gym\")
```

### Workout + Nutrition:
```
# Get chest exercises
get_exercises_by_muscle(\"chest\", 5)

# Plan pre-workout meal
suggest_pre_post_workout_meals(\"strength\", 90, 75, \"gain_muscle\")

# Analyze post-workout meal
analyze_meal([\"1 scoop whey protein\", \"1 banana\", \"1 cup milk\"], \"Post-Workout\")
```

### Progress Tracking:
```
track_weekly_progress(78.5, 75, 3, \"lose_weight\")
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