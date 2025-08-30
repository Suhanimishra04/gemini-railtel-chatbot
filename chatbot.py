from rich import print
from rich.console import Console
from dotenv import load_dotenv
from urllib.parse import unquote
import os
import requests
import re
import json
import sqlite3
import google.generativeai as genai

# Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

API_BASE = "http://127.0.0.1:8000"
console = Console()

def get_device_names_and_types():
    db_path = "./equipment.db"
    if not os.path.exists(db_path):
        return {"all": [], "switches": [], "routers": []}
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT equipment_subtype FROM equipment")
    all_types = [row[0] for row in cursor.fetchall() if row[0]]
    switches = [t for t in all_types if "switch" in t.lower()]
    routers = [t for t in all_types if t not in switches]
    conn.close()
    return {
        "all": all_types,
        "switches": switches,
        "routers": routers
    }

DEVICE_TYPE_LISTS = get_device_names_and_types()

def expand_equipment_subtype(endpoint):
    if "equipment_subtype=router" in endpoint:
        endpoint = endpoint.replace(
            "equipment_subtype=router",
            "equipment_subtype=" + ",".join(DEVICE_TYPE_LISTS.get("routers", []))
        )
    if "equipment_subtype=switch" in endpoint:
        endpoint = endpoint.replace(
            "equipment_subtype=switch",
            "equipment_subtype=" + ",".join(DEVICE_TYPE_LISTS.get("switches", []))
        )
    if "equipment_subtype=devices" in endpoint or "equipment_subtype=device" in endpoint:
        endpoint = endpoint.replace(
            "equipment_subtype=devices",
            "equipment_subtype=" + ",".join(DEVICE_TYPE_LISTS.get("all", []))
        )
        endpoint = endpoint.replace(
            "equipment_subtype=device",
            "equipment_subtype=" + ",".join(DEVICE_TYPE_LISTS.get("all", []))
        )
    return endpoint

def normalize_query_params_in_endpoint(endpoint):
    def lower_param(match):
        return f"{match.group(1)}={match.group(2).lower()}"
    endpoint = re.sub(r'(pop_name|equipment_subtype|equipment_subtype_code|hostname|pop_code|pop_name)=([^&]*)', lower_param, endpoint)
    if "count" not in endpoint and "limit=" not in endpoint and "groupcount" not in endpoint and "groupavg" not in endpoint:
        if "?" in endpoint:
            endpoint += "&limit=10"
        else:
            endpoint += "?limit=10"
    return endpoint

def ask_gemini(user_query):
    equipment_columns = [
        "equipment_id", "hostname", "ip_address", "model_name", "pop_id", "pop_code", "pop_name", "equipment_subtype_code", "equipment_subtype",
        "oem_code", "oem_name", "model_code"
    ]
    pop_columns = [
        "pop_id", "pop_code", "pop_name", "pop_address", "category", "latitude", "longitude", "pop_type", "pop_tier", "region_code",
        "territory_code", "zone_code", "division_code", "state_name", "circle_name", "billing_region_code", "billing_territory_code"
    ]
    prompt = f"""
You are an API query interpreter for a FastAPI backend with two main entities: 'equipment' and 'pop'.

Instructions:
- For any count query (e.g., "How many X with Y?"), use the /equipment/count/ or /pop/count/ endpoint, passing all relevant fields as query parameters. You can count by any field.
- For list queries, always add limit=10 to the endpoint unless the user requests a different limit.
- If the user asks for a specific field (like "ip_address of devices in Agartala"), the endpoint must include the correct filter (e.g., /equipment/?pop_name=Agartala&fields=ip_address&limit=10).
- If the user asks for a specific device type, use the 'equipment_subtype' field to filter.
- If the user asks for a specific item by ID, the endpoint should include it (e.g., /pop/1010010).
- If filters like location, IP address, name, etc., are mentioned, add them as query parameters (e.g., /pop/?state_name=Delhi&limit=10).
- Always return a clean JSON dictionary with only these keys: "entity", "endpoint", "fields".
- Do NOT include extra fields or the entire database; only include the fields the user requested.
- If the user asks "which location has the highest/second highest/third highest/lowest/second lowest/third lowest/average/least number of X", use the /equipment/groupcount/ or /pop/groupcount/ endpoint with group_by set to the relevant field (e.g., pop_name, location, state_name, etc.), and the relevant filters (e.g., equipment_subtype=router for routers). Use order=desc for highest, order=asc for lowest, and limit=3 for top/bottom 3. For average, use /equipment/groupavg/ or /pop/groupavg/ with avg_field set to the field to average. Return the relevant result (top, second, third, least, average, etc.).
- If the user asks for a list, always include limit=10 in the endpoint unless otherwise specified.
- If the user asks for a count, always use the /equipment/count/ or /pop/count/ endpoint with all relevant filters.
- If the user asks "list all types of X" or "what are the types of X" or "show all unique values of X", use the /equipment/distinct/?field=X or /pop/distinct/?field=X endpoint, depending on which entity X belongs to.
- If the user asks "how many types of X are there" or "number of unique X", use the /equipment/distinct/?field=X or /pop/distinct/?field=X endpoint, and count the number of results.
- If the user asks "list all the devices that are present in (specific oem_name)", use /equipment/?oem_name=<name>&limit=10.
- Always return a clean JSON dictionary with only these keys: "entity", "endpoint", "fields".

FIELD VALUE NORMALIZATION:

Always normalize user-provided values to match real database entries — even if they're partial, lowercase, hyphenated, misspelled, abbreviated, or space-separated.

You must do this normalization on *ALL queryable fields*, including:
- model_name, oem_name, hostname, pop_name, pop_code, state_name, equipment_subtype, etc.

Specifically:
- "d link", "dlink", "d-link", "drink" should be "D-Link"
- "ecs2100", "ecs-2100", "ecs 2100" → "ECS-2100"
- "juniper", "junipr", "jun per" → "Juniper"
- "fiberhome", "fiber home", "fiber-home" → "Fiberhome"
- "bng" → "Broadband Network Gateway"
- "uttarpradesh", "uttar pradesh", "up" → "Uttar Pradesh"
- "delhi", "dilli" → "Delhi"
- "agartla", "agartaala", "agartala" → "Agartala"

If a user says:
- "how many d link switches", you MUST rewrite the endpoint using oem_name=D-Link
- "how many cisco routers" → oem_name=Cisco
- "devices with ecs2100 model" → model_name=ECS-2100

Do *not* pass fuzzy or ambiguous user values directly to the API — always transform them into the *correct value from the database* using reasoning and known patterns.

Your job is to understand the intent and correct any field value before forming the endpoint.

Device classification rule:
- Use these lists for classification:
  - Switches: {DEVICE_TYPE_LISTS.get("switches", [])}
  - Routers: {DEVICE_TYPE_LISTS.get("routers", [])}
  - All: {DEVICE_TYPE_LISTS.get("all", [])}
- When the user asks for "switches", always add equipment_subtype=<comma-separated switches> as a query parameter in the endpoint.
- When the user asks for "routers", always add equipment_subtype=<comma-separated routers> as a query parameter in the endpoint.
- When the user asks for "devices", always add equipment_subtype=<comma-separated routers and switches> as a query parameter in the endpoint.
- Always use the correct filters in the endpoint, including pop_name, equipment_subtype, etc., as needed.

Available columns for 'equipment': {equipment_columns}
Available columns for 'pop': {pop_columns}

User query: {user_query}
"""
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith(""):
        text = re.sub(r"json|```", "", text).strip()
    return text

def fetch_api(endpoint):
    endpoint = unquote(endpoint)
    url = API_BASE + endpoint
    response = requests.get(url)
    try:
        data = response.json()
    except Exception:
        data = {}
    # Fallback: If no results, try to relax the query (remove pop_name filter)
    if (isinstance(data, list) and not data) or (isinstance(data, dict) and not data):
        if "pop_name=" in endpoint:
            new_endpoint = re.sub(r'(&|\?)pop_name=[^&]*', '', endpoint)
            new_endpoint = new_endpoint.replace('&&', '&').replace('?&', '?')
            print(f"[magenta]Retrying without pop_name filter: {API_BASE + new_endpoint}[/magenta]")
            response = requests.get(API_BASE + new_endpoint)
            try:
                data = response.json()
            except Exception:
                data = {}
    return data

def extract_fields(data, fields):
    if not fields:
        return data
    if isinstance(data, list):
        if not data:
            return []
        filtered = []
        for item in data:
            row = {k: item.get(k, None) for k in fields}
            if any(v is not None for v in row.values()):
                filtered.append(row)
        return filtered
    elif isinstance(data, dict):
        if not data:
            return {}
        row = {k: data.get(k, None) for k in fields}
        if any(v is not None for v in row.values()):
            return row
        else:
            return {}
    return data

def multi_api_fetch(endpoints, fields):
    results = []
    for endpoint, field_list in endpoints:
        api_response = fetch_api(endpoint)
        filtered = extract_fields(api_response, field_list)
        results.extend(filtered if isinstance(filtered, list) else [filtered])
    return results

def main():
    console.print("[bold green]Welcome to the Gemini-Powered Equipment & POP Chatbot![/bold green]")
    while True:
        user_input = console.input("\n[bold blue]You:[/bold blue] ")

        if user_input.lower() in ["exit", "quit"]:
            print("[bold red]Goodbye![/bold red]")
            break

        try:
            gemini_response = ask_gemini(user_input)
            interpretation = json.loads(gemini_response)

            # If Gemini returns a list of endpoints, call all and aggregate
            if isinstance(interpretation, list):
                endpoints = []
                for item in interpretation:
                    endpoint = expand_equipment_subtype(item["endpoint"])
                    endpoint = normalize_query_params_in_endpoint(endpoint)
                    endpoints.append((endpoint, item["fields"]))
                results = multi_api_fetch(endpoints, [item["fields"] for item in interpretation])
                if not results or results == [{}] or results == [[]] or all((r == {} or r == [] or r is None) for r in results):
                    console.print("\n[bold yellow]No results found for your query.[/bold yellow]")
                else:
                    console.print("\n[bold yellow]🔍 Result:[/bold yellow]")
                    console.print(results)
                continue

            endpoint = expand_equipment_subtype(interpretation["endpoint"])
            endpoint = normalize_query_params_in_endpoint(endpoint)
            fields = interpretation["fields"]
            
            if "/distinct/" in endpoint and ("how many" in user_input.lower() or "number of" in user_input.lower()):
                api_response = fetch_api(endpoint)
                count = len(api_response) if isinstance(api_response, list) else 0
                console.print(f"\n[bold yellow]🔢 Number of types:[/bold yellow] {count}")
                continue

            api_response = fetch_api(endpoint)

            # --- Updated: Let Gemini handle greatest/lowest logic ---
            if "/equipment/groupcount/" in endpoint or "/pop/groupcount/" in endpoint:
                llm_prompt = f"""
You are a helpful assistant. The user asked: "{user_input}"

Here is the data returned from the API (as a JSON array or object):

{json.dumps(api_response, indent=2)}

Analyze the data and answer the user's question in a clear, human-readable way.
If the user asks for the highest, lowest, second highest, second lowest, etc., find and report the correct value(s) from the data.
If the data is empty, say "No results found for your query."
"""
                response = model.generate_content(llm_prompt)
                llm_answer = response.text.strip()
                console.print(f"\n[bold yellow]{llm_answer}[/bold yellow]")
                continue

            if "/equipment/groupavg/" in endpoint or "/pop/groupavg/" in endpoint:
                if isinstance(api_response, list) and api_response:
                    console.print(f"\n[bold yellow]Averages:[/bold yellow] {api_response}")
                else:
                    console.print("\n[bold yellow]No results found for your query.[/bold yellow]")
                continue

            filtered = extract_fields(api_response, fields)
            if fields == ["count"] and isinstance(filtered, dict) and "count" in filtered:
                console.print(f"\n[bold yellow]🔢 Number:[/bold yellow] {filtered['count']}")
            elif not filtered or filtered == [{}] or filtered == [] or filtered is None:
                console.print("\n[bold yellow]No results found for your query.[/bold yellow]")
            else:
                console.print("\n[bold yellow]🔍 Result:[/bold yellow]")
                console.print(filtered)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()