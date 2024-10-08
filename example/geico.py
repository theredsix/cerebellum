from browser.planner.local import LocalLLMBrowserPlanner
from cerebellum import FileSessionMemory, BrowserSession, GeminiBrowserPlanner, HumanBrowserPlanner, OpenAIBrowserPlanner
from playwright.sync_api import sync_playwright
import os


def wait_for_input():
    # Check for keyboard input
    input("Press enter to continue...")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True)
    page = context.new_page()
    control_page = context.new_page()
    # debug_page = context.new_page()
    # page.goto("https://www.dmv.ca.gov/")
    page.goto("https://www.geico.com")

    recorders = [FileSessionMemory('geico.cere.zip')]
    # base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'], model_name='gemini-1.5-pro-exp-0827')
    base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    # base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Navigate through the website until you generate an auto insurance quote. Do not generate a home insurance quote. If you're on a page showing an auto insurance quote (with premium amounts), your goal is COMPLETE."
    additional_context = {
        "licensed_at_age": 19,
        "education_level": "HIGH_SCHOOL",
        "phone_number": "8042221111",
        "full_name": "Chris P. Bacon",
        "past_claim": [],
        "has_claims": False,
        "spouse_occupation": "Florist",
        "auto_current_carrier": "None",
        "home_commercial_uses": None,
        "spouse_full_name": "Amy Stake",
        "auto_commercial_uses": None,
        "requires_sr22": False,
        "previous_address_move_date": None,
        "line_of_work": None,
        "spouse_age": "1987-12-12",
        "auto_insurance_deadline": None,
        "email": "chris.p.bacon@abc.com",
        "net_worth_numeric": 1000000,
        "spouse_gender": "F",
        "marital_status": "married",
        "spouse_licensed_at_age": 20,
        "license_number": "AAAAAAA090AA",
        "spouse_license_number": "AAAAAAA080AA",
        "how_much_can_you_lose": 25000,
        "vehicles": [
            {
                "annual_mileage": 10000,
                "commute_mileage": 4000,
                "existing_coverages": None,
                "ideal_coverages": {
                    "bodily_injury_per_incident_limit": 50000,
                    "bodily_injury_per_person_limit": 25000,
                    "collision_deductible": 1000,
                    "comprehensive_deductible": 1000,
                    "personal_injury_protection": None,
                    "property_damage_per_incident_limit": None,
                    "property_damage_per_person_limit": 25000,
                    "rental_reimbursement_per_incident_limit": None,
                    "rental_reimbursement_per_person_limit": None,
                    "roadside_assistance_limit": None,
                    "underinsured_motorist_bodily_injury_per_incident_limit": 50000,
                    "underinsured_motorist_bodily_injury_per_person_limit": 25000,
                    "underinsured_motorist_property_limit": None,
                },
                "ownership": "Owned",
                "parked": "Garage",
                "purpose": "commute",
                "vehicle": {
                    "style": "AWD 3.0 quattro TDI 4dr Sedan",
                    "model": "A8 L",
                    "price_estimate": 29084,
                    "year": 2015,
                    "make": "Audi",
                },
                "vehicle_id": None,
                "vin": None,
            }
        ],
        "additional_drivers": [],
        "home": [
            {
                "home_ownership": "owned",
            }
        ],
        "spouse_line_of_work": "Agriculture, Forestry and Fishing",
        "occupation": "Customer Service Representative",
        "id": None,
        "gender": "M",
        "credit_check_authorized": False,
        "age": "1987-11-11",
        "license_state": "Washington",
        "cash_on_hand": "$10000–14999",
        "address": {
            "city": "HOUSTON",
            "country": "US",
            "state": "TX",
            "street": "9625 GARFIELD AVE.",
            "zip": "77082",
        },
        "spouse_education_level": "MASTERS",
        "spouse_email": "amy.stake@abc.com",
        "spouse_added_to_auto_policy": True,
    }

    session = BrowserSession(goal, additional_context, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()