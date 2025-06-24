import json
import httpx
from server.utils import get_wger_headers, WGER_BASE_URL
from mcp_server import mcp

@mcp.tool()
async def search_exercises(query: str, limit: int = 20) -> str:
    # ... existing code ...
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{WGER_BASE_URL}/exercise/",
                headers=get_wger_headers(),
                params={"search": query, "limit": limit, "language": 2}
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
            results = {"query": query, "total_found": data.get("count", 0), "exercises": exercises}
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching exercises: {str(e)}"

@mcp.tool()
async def get_exercises_by_muscle(muscle_group: str, limit: int = 15) -> str:
    # ... existing code ...
    muscle_mapping = {
        "chest": [4],
        "back": [12, 13],
        "shoulders": [2, 3],
        "arms": [1, 5, 8],
        "legs": [10, 11, 7, 9],
        "abs": [14, 6],
        "core": [14, 6]
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
                    params={"muscles": muscle_id, "limit": limit // len(muscle_ids), "language": 2}
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
            results = {"muscle_group": muscle_group, "total_exercises": len(exercises), "exercises": exercises[:limit]}
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting exercises by muscle: {str(e)}"

@mcp.tool()
async def get_equipment_exercises(equipment_name: str, limit: int = 15) -> str:
    # ... existing code ...
    async with httpx.AsyncClient() as client:
        try:
            equipment_response = await client.get(
                f"{WGER_BASE_URL}/equipment/",
                headers=get_wger_headers(),
                params={"limit": 50}
            )
            equipment_response.raise_for_status()
            equipment_data = equipment_response.json()
            equipment_id = None
            for equipment in equipment_data.get("results", []):
                if equipment_name.lower() in equipment.get("name", "").lower():
                    equipment_id = equipment.get("id")
                    break
            if not equipment_id:
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
            response = await client.get(
                f"{WGER_BASE_URL}/exercise/",
                headers=get_wger_headers(),
                params={"equipment": equipment_id, "limit": limit, "language": 2}
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
            results = {"equipment": equipment_name, "total_exercises": len(exercises), "exercises": exercises}
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting equipment exercises: {str(e)}"

@mcp.tool()
async def get_workout_templates(difficulty: str = "intermediate") -> str:
    # ... existing code ...
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
                workout_info = {
                    "id": workout.get("id"),
                    "name": workout.get("name", f"Workout {workout.get('id')}") ,
                    "creation_date": workout.get("creation_date"),
                    "description": workout.get("comment", "")
                }
                workouts.append(workout_info)
            results = {"difficulty": difficulty, "available_workouts": len(workouts), "workouts": workouts}
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"WGER API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error getting workout templates: {str(e)}" 