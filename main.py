from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List, Dict, Annotated, Literal
import json

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="Unique identifier for the patient", example="P001")]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City of the patient")]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient")]
    gender: Annotated[Literal["male", "female", "other"], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in mtr")]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kg")]
    
    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 25:
            return "Normal weight"
        elif 25 <= self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120)]
    gender: Annotated[Optional[Literal["male", "female"]], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

def load_data():
    with open("patients.json", "r") as file:
        data = json.load(file)
    return data

def save_data(data):
    with open("patients.json", "w") as file:
        json.dump(data, file)

@app.get("/")
def hello():
    return {"message": "Patient Management System API"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve in the DB", examples="P001")):
    # Load the patient data from the JSON file
    data = load_data()
    # Find the patient with the specified ID
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by: str = Query(..., description="sort on the basis of height, weight or bmi"), order: str = Query("asc", description="sort order: asc or desc")):
    valid_fields = ["height", "weight", "bmi"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Must be one of {valid_fields}")
    
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort order. Must be 'asc' or 'desc'")

    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=(order == "desc"))
    
    return sorted_data

@app.post("/create")
def create_patient(patient: Patient):
    
    # Load existing data
    data = load_data()
    
    # Check if patient ID already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    # Add new patient to the data
    data[patient.id] = patient.model_dump(exclude=['id'])
    
    # save the updated data back to the JSON file
    save_data(data)
    
    return JSONResponse(content={"message": "Patient created successfully", "patient_id": patient.id}, status_code=201)

@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    
    # Load existing data
    data = load_data()
    
    # Check if patient ID exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get the existing patient data
    existing_patient = data[patient_id]
    
    # Convert the update model to a dictionary, excluding unset fields
    patient_update_dict = patient_update.model_dump(exclude_unset=True)
    
    # Update only the fields that are provided in the request
    for field, value in patient_update_dict.items():
        existing_patient[field] = value
    
    # Add the ID back to the patient data for model creation
    existing_patient['id'] = patient_id  
    
    # Create a Pydantic model instance to recalculate BMI and verdict
    pydantic_patient = Patient(**existing_patient)
    
    # Update the patient data in the dictionary
    existing_patient = pydantic_patient.model_dump(exclude=['id'])
    
    # Update the patient data in the main data dictionary
    data[patient_id] = existing_patient
    
    # Save the updated data back to the JSON file
    save_data(data)
    
    return JSONResponse(content={"message": "Patient updated successfully"}, status_code=200)
    
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    
    # Load existing data
    data = load_data()
    
    # Check if patient ID exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Remove the patient from the data
    del data[patient_id]
    
    # Save the updated data back to the JSON file
    save_data(data)
    
    return JSONResponse(content={"message": "Patient deleted successfully"}, status_code=200)