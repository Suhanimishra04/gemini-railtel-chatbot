from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy import create_engine, Column, Integer, String, Float, func, select, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

EQUIPMENT_DB_URL = "sqlite:///./equipment.db"
POP_DB_URL = "sqlite:///./pop.db"

equipment_engine = create_engine(EQUIPMENT_DB_URL, connect_args={"check_same_thread": False})
pop_engine = create_engine(POP_DB_URL, connect_args={"check_same_thread": False})

EquipmentSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=equipment_engine)
PopSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pop_engine)

Base = declarative_base()

class EquipmentORM(Base):
    __tablename__ = "equipment"
    equipment_id = Column(Integer, primary_key=True, index=True)
    pop_id = Column(Integer)
    hostname = Column(String)
    pop_code = Column(String)
    pop_name = Column(String)
    equipment_subtype_code = Column(String)
    equipment_subtype = Column(String)
    oem_code = Column(String)
    oem_name = Column(String)
    model_code = Column(String)
    ip_address = Column(String)
    model_name = Column(String)

class PopORM(Base):
    __tablename__ = "pop"
    pop_id = Column(Integer, primary_key=True, index=True)
    pop_code = Column(String)
    pop_name = Column(String)
    pop_address = Column(String)
    category = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    pop_type = Column(String)
    pop_tier = Column(String)
    region_code = Column(String)
    territory_code = Column(String)
    zone_code = Column(String)
    division_code = Column(String)
    state_name = Column(String)
    circle_name = Column(String)
    billing_region_code = Column(String)
    billing_territory_code = Column(String)

def get_equipment_db():
    db = EquipmentSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pop_db():
    db = PopSessionLocal()
    try:
        yield db
    finally:
        db.close()

class Equipment(BaseModel):
    equipment_id: int = Field(..., description="Unique identifier for the equipment")
    pop_id: Optional[int] = None
    hostname: Optional[str] = None
    pop_code: Optional[str] = None
    pop_name: Optional[str] = None
    equipment_subtype_code: Optional[str] = None
    equipment_subtype: Optional[str] = None
    oem_code: Optional[str] = None
    oem_name: Optional[str] = None
    model_code: Optional[str] = None
    ip_address: Optional[str] = None
    model_name: Optional[str] = None

    class Config:
        from_attributes = True

class Pop(BaseModel):
    pop_id: int = Field(..., description="Unique identifier for the POP")
    pop_code: Optional[str] = None
    pop_name: Optional[str] = None
    pop_address: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pop_type: Optional[str] = None
    pop_tier: Optional[str] = None
    region_code: Optional[str] = None
    territory_code: Optional[str] = None
    zone_code: Optional[str] = None
    division_code: Optional[str] = None
    state_name: Optional[str] = None
    circle_name: Optional[str] = None
    billing_region_code: Optional[str] = None
    billing_territory_code: Optional[str] = None

    class Config:
        from_attributes = True

app = FastAPI(
    title="Project API",
    description="API to access and manage equipment and POP data from two SQLite databases."
)

def apply_equipment_filters(query, params):
    if params.get("equipment_id"):
        query = query.filter(EquipmentORM.equipment_id == int(params["equipment_id"]))
    if params.get("pop_id"):
        query = query.filter(EquipmentORM.pop_id == int(params["pop_id"]))
    if params.get("hostname"):
        query = query.filter(func.lower(EquipmentORM.hostname).like(f"%{params['hostname'].lower()}%"))
    if params.get("pop_code"):
        query = query.filter(func.lower(EquipmentORM.pop_code).like(f"%{params['pop_code'].lower()}%"))
    if params.get("pop_name"):
        query = query.filter(func.lower(EquipmentORM.pop_name).like(f"%{params['pop_name'].lower()}%"))
    if params.get("equipment_subtype_code"):
        query = query.filter(func.lower(EquipmentORM.equipment_subtype_code).like(f"%{params['equipment_subtype_code'].lower()}%"))
    if params.get("equipment_subtype"):
        subtypes = [s.strip() for s in params["equipment_subtype"].split(",")]
        query = query.filter(func.lower(EquipmentORM.equipment_subtype).in_([s.lower() for s in subtypes]))
    if params.get("oem_code"):
        query = query.filter(func.lower(EquipmentORM.oem_code).like(f"%{params['oem_code'].lower()}%"))
    if params.get("oem_name"):
        query = query.filter(func.lower(EquipmentORM.oem_name).like(f"%{params['oem_name'].lower()}%"))
    if params.get("model_code"):
        query = query.filter(func.lower(EquipmentORM.model_code).like(f"%{params['model_code'].lower()}%"))
    if params.get("ip_address"):
        query = query.filter(func.lower(EquipmentORM.ip_address).like(f"%{params['ip_address'].lower()}%"))
    if params.get("model_name"):
        query = query.filter(func.lower(EquipmentORM.model_name).like(f"%{params['model_name'].lower()}%"))
    if params.get("state_name"):
        query = query.filter(func.lower(EquipmentORM.pop_name).like(f"%{params['state_name'].lower()}%"))
    return query

def apply_pop_filters(query, params):
    if params.get("pop_id"):
        query = query.filter(PopORM.pop_id == int(params["pop_id"]))
    if params.get("pop_code"):
        query = query.filter(func.lower(PopORM.pop_code).like(f"%{params['pop_code'].lower()}%"))
    if params.get("pop_name"):
        query = query.filter(func.lower(PopORM.pop_name).like(f"%{params['pop_name'].lower()}%"))
    if params.get("pop_address"):
        query = query.filter(func.lower(PopORM.pop_address).like(f"%{params['pop_address'].lower()}%"))
    if params.get("category"):
        query = query.filter(func.lower(PopORM.category).like(f"%{params['category'].lower()}%"))
    if params.get("latitude"):
        query = query.filter(PopORM.latitude == float(params["latitude"]))
    if params.get("longitude"):
        query = query.filter(PopORM.longitude == float(params["longitude"]))
    if params.get("pop_type"):
        query = query.filter(func.lower(PopORM.pop_type).like(f"%{params['pop_type'].lower()}%"))
    if params.get("pop_tier"):
        query = query.filter(func.lower(PopORM.pop_tier).like(f"%{params['pop_tier'].lower()}%"))
    if params.get("region_code"):
        query = query.filter(func.lower(PopORM.region_code).like(f"%{params['region_code'].lower()}%"))
    if params.get("territory_code"):
        query = query.filter(func.lower(PopORM.territory_code).like(f"%{params['territory_code'].lower()}%"))
    if params.get("zone_code"):
        query = query.filter(func.lower(PopORM.zone_code).like(f"%{params['zone_code'].lower()}%"))
    if params.get("division_code"):
        query = query.filter(func.lower(PopORM.division_code).like(f"%{params['division_code'].lower()}%"))
    if params.get("state_name"):
        query = query.filter(func.lower(PopORM.state_name).like(f"%{params['state_name'].lower()}%"))
    if params.get("circle_name"):
        query = query.filter(func.lower(PopORM.circle_name).like(f"%{params['circle_name'].lower()}%"))
    if params.get("billing_region_code"):
        query = query.filter(func.lower(PopORM.billing_region_code).like(f"%{params['billing_region_code'].lower()}%"))
    if params.get("billing_territory_code"):
        query = query.filter(func.lower(PopORM.billing_territory_code).like(f"%{params['billing_territory_code'].lower()}%"))
    return query



@app.get("/equipment/")
def get_equipment(
    equipment_id: Optional[str] = Query(None),
    pop_id: Optional[str] = Query(None),
    hostname: Optional[str] = Query(None),
    pop_code: Optional[str] = Query(None),
    pop_name: Optional[str] = Query(None),
    equipment_subtype_code: Optional[str] = Query(None),
    equipment_subtype: Optional[str] = Query(None),
    oem_code: Optional[str] = Query(None),
    oem_name: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    state_name: Optional[str] = Query(None),
    fields: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_equipment_db)
):
    # only include filterable fields
    filterable_params = {
        "equipment_id": equipment_id,
        "pop_id": pop_id,
        "hostname": hostname,
        "pop_code": pop_code,
        "pop_name": pop_name,
        "equipment_subtype_code": equipment_subtype_code,
        "equipment_subtype": equipment_subtype,
        "oem_code": oem_code,
        "oem_name": oem_name,
        "model_code": model_code,
        "ip_address": ip_address,
        "model_name": model_name,
        "state_name": state_name
    }

    query = db.query(EquipmentORM)
    query = apply_equipment_filters(query, filterable_params)
    results = query.limit(limit).all()

    if fields:
        fields_list = [f.strip() for f in fields.split(",")]
        filtered = [{k: getattr(r, k, None) for k in fields_list} for r in results]
        return JSONResponse(content=filtered)

    return results


@app.get("/equipment/{equipment_id}", response_model=Equipment)
def get_equipment_by_id(equipment_id: int, db: Session = Depends(get_equipment_db)):
    result = db.query(EquipmentORM).filter(EquipmentORM.equipment_id == equipment_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return result

@app.get("/equipment/count/")
def get_equipment_count(
    equipment_id: Optional[str] = Query(None),
    pop_id: Optional[str] = Query(None),
    hostname: Optional[str] = Query(None),
    pop_code: Optional[str] = Query(None),
    pop_name: Optional[str] = Query(None),
    equipment_subtype_code: Optional[str] = Query(None),
    equipment_subtype: Optional[str] = Query(None),
    oem_code: Optional[str] = Query(None),
    oem_name: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    state_name: Optional[str] = Query(None),
    db: Session = Depends(get_equipment_db)
):
    params = locals()
    query = db.query(func.count(EquipmentORM.equipment_id))
    query = apply_equipment_filters(query, params)
    count = query.scalar()
    return {"count": count}

@app.get("/equipment/groupcount/")
def get_equipment_groupcount(
    group_by: str = Query(..., description="Field to group by, e.g., pop_name or location"),
    equipment_subtype: Optional[str] = Query(None),
    oem_name: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    order: str = Query("desc", description="desc for highest, asc for lowest"),
    limit: int = Query(10, description="How many top/bottom results to return"),
    db: Session = Depends(get_equipment_db)
):
    if not hasattr(EquipmentORM, group_by):
        raise HTTPException(status_code=400, detail=f"Invalid group_by field: {group_by}")
    group_col = getattr(EquipmentORM, group_by)
    query = db.query(group_col, func.count(EquipmentORM.equipment_id).label("count"))
    params = locals()
    query = apply_equipment_filters(query, params)
    query = query.group_by(group_col)
    if order == "desc":
        query = query.order_by(func.count(EquipmentORM.equipment_id).desc())
    else:
        query = query.order_by(func.count(EquipmentORM.equipment_id).asc())
    results = query.limit(limit).all()
    return [{group_by: r[0], "count": r[1]} for r in results]

@app.get("/equipment/groupavg/")
def get_equipment_groupavg(
    group_by: str = Query(..., description="Field to group by, e.g., pop_name or location"),
    avg_field: str = Query(..., description="Field to average, e.g., equipment_id"),
    equipment_subtype: Optional[str] = Query(None),
    oem_name: Optional[str] = Query(None),
    model_code: Optional[str] = Query(None),
    order: str = Query("desc", description="desc for highest, asc for lowest"),
    limit: int = Query(10, description="How many top/bottom results to return"),
    db: Session = Depends(get_equipment_db)
):
    if not hasattr(EquipmentORM, group_by) or not hasattr(EquipmentORM, avg_field):
        raise HTTPException(status_code=400, detail=f"Invalid group_by or avg_field")
    group_col = getattr(EquipmentORM, group_by)
    avg_col = getattr(EquipmentORM, avg_field)
    query = db.query(group_col, func.avg(avg_col).label("average"))
    params = locals()
    query = apply_equipment_filters(query, params)
    query = query.group_by(group_col)
    if order == "desc":
        query = query.order_by(func.avg(avg_col).desc())
    else:
        query = query.order_by(func.avg(avg_col).asc())
    results = query.limit(limit).all()
    return [{group_by: r[0], "average": r[1]} for r in results]

@app.get("/equipment/distinct/")
def get_distinct_equipment_field(
    field: str,
    db: Session = Depends(get_equipment_db),
    pop_name: Optional[str] = None,
    hostname: Optional[str] = None,
    ip_address: Optional[str] = None,
    equipment_subtype: Optional[str] = None,
):
    column = getattr(EquipmentORM, field)
    query = db.query(column)

    if pop_name:
        query = query.filter(func.lower(EquipmentORM.pop_name) == pop_name.lower())
    if hostname:
        query = query.filter(func.lower(EquipmentORM.hostname) == hostname.lower())
    if ip_address:
        query = query.filter(func.lower(EquipmentORM.ip_address) == ip_address.lower())
    if equipment_subtype:
        subtype_list = [x.strip().lower() for x in equipment_subtype.split(",")]
        query = query.filter(func.lower(EquipmentORM.equipment_subtype).in_(subtype_list))

    results = query.distinct().all()
    return [r[0] for r in results if r[0]]

@app.get("/equipment/subtypes/", response_model=Dict[str, List[str]])
def get_equipment_subtypes(db: Session = Depends(get_equipment_db)):
    all_types = [row[0] for row in db.query(EquipmentORM.equipment_subtype).distinct() if row[0]]
    switches = [t for t in all_types if "switch" in t.lower()]
    routers = [t for t in all_types if t not in switches]
    return {
        "all": all_types,
        "switches": switches,
        "routers": routers,
        "others": [t for t in all_types if t not in switches and t not in routers]
    }


@app.get("/pop/", response_model=List[Pop])
def get_pops(
    pop_id: Optional[str] = Query(None),
    pop_code: Optional[str] = Query(None),
    pop_name: Optional[str] = Query(None),
    pop_address: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    latitude: Optional[str] = Query(None),
    longitude: Optional[str] = Query(None),
    pop_type: Optional[str] = Query(None),
    pop_tier: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    territory_code: Optional[str] = Query(None),
    zone_code: Optional[str] = Query(None),
    division_code: Optional[str] = Query(None),
    state_name: Optional[str] = Query(None),
    circle_name: Optional[str] = Query(None),
    billing_region_code: Optional[str] = Query(None),
    billing_territory_code: Optional[str] = Query(None),
    fields: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_pop_db)
):
    params = locals()
    query = db.query(PopORM)
    query = apply_pop_filters(query, params)
    results = query.limit(limit).all()
    if fields:
        fields_list = [f.strip() for f in fields.split(",")]
        return [{k: getattr(r, k, None) for k in fields_list} for r in results]
    return results

@app.get("/pop/{pop_id}", response_model=Pop)
def get_pop_by_id(pop_id: int, db: Session = Depends(get_pop_db)):
    result = db.query(PopORM).filter(PopORM.pop_id == pop_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="POP not found")
    return result

@app.get("/pop/count/")
def get_pop_count(
    pop_id: Optional[str] = Query(None),
    pop_code: Optional[str] = Query(None),
    pop_name: Optional[str] = Query(None),
    pop_address: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    latitude: Optional[str] = Query(None),
    longitude: Optional[str] = Query(None),
    pop_type: Optional[str] = Query(None),
    pop_tier: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    territory_code: Optional[str] = Query(None),
    zone_code: Optional[str] = Query(None),
    division_code: Optional[str] = Query(None),
    state_name: Optional[str] = Query(None),
    circle_name: Optional[str] = Query(None),
    billing_region_code: Optional[str] = Query(None),
    billing_territory_code: Optional[str] = Query(None),
    db: Session = Depends(get_pop_db)
):
    params = locals()
    query = db.query(func.count(PopORM.pop_id))
    query = apply_pop_filters(query, params)
    count = query.scalar()
    return {"count": count}

@app.get("/pop/distinct/")
def get_pop_distinct(field: str, db: Session = Depends(get_pop_db)):
    if not hasattr(PopORM, field):
        raise HTTPException(status_code=400, detail=f"Invalid field: {field}")
    col = getattr(PopORM, field)
    results = db.query(col).distinct().all()
    return [r[0] for r in results if r[0] is not None]

@app.get("/pop/groupcount/")
def get_pop_groupcount(
    group_by: str = Query(..., description="Field to group by, e.g., state_name or pop_tier"),
    order: str = Query("desc", description="desc for highest, asc for lowest"),
    limit: int = Query(10, description="How many top/bottom results to return"),
    db: Session = Depends(get_pop_db)
):
    if not hasattr(PopORM, group_by):
        raise HTTPException(status_code=400, detail=f"Invalid group_by field: {group_by}")
    group_col = getattr(PopORM, group_by)
    query = db.query(group_col, func.count(PopORM.pop_id).label("count")).group_by(group_col)
    if order == "desc":
        query = query.order_by(func.count(PopORM.pop_id).desc())
    else:
        query = query.order_by(func.count(PopORM.pop_id).asc())
    results = query.limit(limit).all()
    return [{group_by: r[0], "count": r[1]} for r in results]

@app.get("/pop/groupavg/")
def get_pop_groupavg(
    group_by: str = Query(..., description="Field to group by, e.g., state_name or pop_tier"),
    avg_field: str = Query(..., description="Field to average, e.g., pop_id"),
    order: str = Query("desc", description="desc for highest, asc for lowest"),
    limit: int = Query(10, description="How many top/bottom results to return"),
    db: Session = Depends(get_pop_db)
):
    if not hasattr(PopORM, group_by) or not hasattr(PopORM, avg_field):
        raise HTTPException(status_code=400, detail=f"Invalid group_by or avg_field")
    group_col = getattr(PopORM, group_by)
    avg_col = getattr(PopORM, avg_field)
    query = db.query(group_col, func.avg(avg_col).label("average")).group_by(group_col)
    if order == "desc":
        query = query.order_by(func.avg(avg_col).desc())
    else:
        query = query.order_by(func.avg(avg_col).asc())
    results = query.limit(limit).all()
    return [{group_by: r[0], "average": r[1]} for r in results]