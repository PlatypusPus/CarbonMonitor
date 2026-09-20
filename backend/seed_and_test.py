import datetime
from sqlalchemy import select
from database import SessionLocal
from models.facility import Facility
from models.period import Period
from models.activity_record import ActivityRecord
from models.emission_factor import EmissionFactor
from services.calculation import calculate_emissions
from services.anomaly import run_detection
from services.recommendations import evaluate_rules
from services.scenario import run_scenario

def run():
    db = SessionLocal()
    
    print("--- 1. Creating Facilities ---")
    facilities_data = ["Main Library", "Science Building", "Student Union"]
    facilities = {}
    for name in facilities_data:
        fac = db.execute(select(Facility).where(Facility.name == name)).scalar_one_or_none()
        if not fac:
            fac = Facility(name=name, facility_type="office", region_code="US-CA")
            db.add(fac)
            db.commit()
            db.refresh(fac)
        facilities[name] = fac
        print(f"Facility: {fac.name} (ID: {fac.id})")
        
    print("\n--- 2. Creating Periods ---")
    periods_data = [
        ("2026-Q1", datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 3, 31, tzinfo=datetime.timezone.utc)),
        ("2026-Q2", datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 6, 30, tzinfo=datetime.timezone.utc)),
        ("2026-Q3", datetime.datetime(2026, 7, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 9, 30, tzinfo=datetime.timezone.utc)),
    ]
    periods = {}
    for name, start, end in periods_data:
        p = db.execute(select(Period).where(Period.name == name)).scalar_one_or_none()
        if not p:
            p = Period(name=name, start_date=start, end_date=end)
            db.add(p)
            db.commit()
            db.refresh(p)
        periods[name] = p
        print(f"Period: {p.name}")
        
    print("\n--- 3. Creating Realistic Activity Records ---")
    # Fetch emission factors
    factors = {ef.activity_type: ef for ef in db.execute(select(EmissionFactor)).scalars().all()}
    if "electricity" not in factors:
        print("Missing emission factors! Did seed run?")
        return
        
    # Standard campus usage
    records = [
        # Main Library Q1
        {"facility": "Main Library", "period": "2026-Q1", "type": "electricity", "qty": 150000, "unit": "kWh"},
        {"facility": "Main Library", "period": "2026-Q1", "type": "diesel", "qty": 500, "unit": "litre"},
        # Main Library Q2 (similar)
        {"facility": "Main Library", "period": "2026-Q2", "type": "electricity", "qty": 145000, "unit": "kWh"},
        {"facility": "Main Library", "period": "2026-Q2", "type": "diesel", "qty": 450, "unit": "litre"},
        # Main Library Q3 (similar)
        {"facility": "Main Library", "period": "2026-Q3", "type": "electricity", "qty": 155000, "unit": "kWh"},
        
        # Science Building Q1
        {"facility": "Science Building", "period": "2026-Q1", "type": "electricity", "qty": 400000, "unit": "kWh"},
        {"facility": "Science Building", "period": "2026-Q1", "type": "lpg", "qty": 2000, "unit": "litre"},
        # Science Building Q2
        {"facility": "Science Building", "period": "2026-Q2", "type": "electricity", "qty": 410000, "unit": "kWh"},
        {"facility": "Science Building", "period": "2026-Q2", "type": "lpg", "qty": 1900, "unit": "litre"},
        # Science Building Q3 - BIG SPIKE (Anomaly & Spike Recommendation should trigger)
        {"facility": "Science Building", "period": "2026-Q3", "type": "electricity", "qty": 900000, "unit": "kWh"},
        {"facility": "Science Building", "period": "2026-Q3", "type": "lpg", "qty": 2100, "unit": "litre"},
    ]
    
    act_records = []
    for r in records:
        fac = facilities[r["facility"]]
        p = periods[r["period"]]
        act = ActivityRecord(
            facility_id=fac.id,
            activity_type=r["type"],
            quantity=r["qty"],
            unit=r["unit"],
            period_start=p.start_date,
            period_end=p.end_date,
            source="csv",
            confirmed_by_user=True
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        act_records.append(act)
    print(f"Created {len(act_records)} activity records.")

    print("\n--- 4. Running Calculations ---")
    calc_emissions = []
    for act in act_records:
        factor = factors.get(act.activity_type)
        calc = calculate_emissions(act, factor)
        db.add(calc)
        db.commit()
        calc_emissions.append(calc)
    print(f"Calculated {len(calc_emissions)} emissions.")
    
    print("\n--- 5. Running Anomaly Detection ---")
    anomalies_detected = run_detection(db)
    print(f"Anomalies detected: {anomalies_detected}")
    
    print("\n--- 6. Running Recommendations Engine ---")
    for fac_name, fac in facilities.items():
        recs = evaluate_rules(db, fac.id, periods["2026-Q3"].id)
        if recs:
            print(f"Recommendations for {fac_name} in Q3:")
            for r in recs:
                print(f"  - [{r.rule_id}] {r.message} \n      Data: {r.supporting_numbers}")
                db.add(r)
            db.commit()
            
    print("\n--- 7. Running Scenario Simulation ---")
    baseline = {
        "id": act_records[-2].id, # The spike electricity record
        "activity_type": "electricity",
        "quantity": 900000,
        "unit": "kWh"
    }
    print("Baseline scenario (900,000 kWh):", baseline)
    # What if we installed solar panels and reduced electricity by 300,000 kWh?
    modified = {"quantity": 600000}
    res = run_scenario(db, baseline, modified)
    print(f"Scenario Result (600,000 kWh): {res['result_co2e_kg']} kg CO2e (Scope {res['scope']})")
    
    db.close()

if __name__ == "__main__":
    run()
