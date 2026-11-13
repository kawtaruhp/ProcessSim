
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from calculations import simulate, parametric_study


# =========================================
# CONFIGURATION
# =========================================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="ProcessSim",
    description="Application de modélisation et simulation des procédés",
    version="2.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


# =========================================
# VALIDATION DES PARAMETRES
# =========================================

class SimulationInput(BaseModel):

    m0: float = Field(default=1000, gt=0)
    x0: float = Field(default=10, gt=0, le=100)
    residus: float = Field(default=20, ge=0)

    mR: float = Field(default=100, gt=0)
    xR: float = Field(default=40, ge=0, le=100)

    Cp: float = Field(default=3.8, gt=0)
    T2: float = Field(default=20, ge=0)
    T3: float = Field(default=80, gt=0)

    x4: float = Field(default=40, gt=0, le=100)

    lambda_: float = Field(
        default=2300,
        gt=0,
        alias="lambda"
    )

    T5: float = Field(default=25, ge=0)

    @model_validator(mode="after")
    def verifier_parametres(self):

        if self.residus >= self.m0:
            raise ValueError(
                "Les résidus doivent être inférieurs au débit initial."
            )

        if self.T3 <= self.T2:
            raise ValueError(
                "La température T3 doit être supérieure à T2."
            )

        if self.T5 > self.T3:
            raise ValueError(
                "La température T5 doit être inférieure ou égale à T3."
            )

        return self

    def to_calculation_dict(self):

        return {
            "m0": self.m0,
            "x0": self.x0,
            "residus": self.residus,
            "mR": self.mR,
            "xR": self.xR,
            "Cp": self.Cp,
            "T2": self.T2,
            "T3": self.T3,
            "x4": self.x4,
            "lambda": self.lambda_,
            "T5": self.T5
        }


# =========================================
# PAGE D'ACCUEIL
# =========================================

@app.get("/")
def accueil():

    return FileResponse(STATIC_DIR / "index.html")


# =========================================
# VERIFICATION DU SERVEUR
# =========================================

@app.get("/api/health")
def health():

    return {
        "status": "OK",
        "application": "ProcessSim",
        "version": "2.0"
    }


# =========================================
# SIMULATION PRINCIPALE
# =========================================

@app.post("/api/simulate")
def lancer_simulation(data: SimulationInput):

    try:

        parametres = data.to_calculation_dict()

        resultats = simulate(parametres)

        return {
            "success": True,
            "message": "Simulation réalisée avec succès.",
            "results": resultats
        }

    except (ValueError, ZeroDivisionError) as erreur:

        raise HTTPException(
            status_code=400,
            detail=str(erreur)
        )


# =========================================
# ETUDE PARAMETRIQUE
# =========================================

@app.post("/api/parametric")
def etude_parametrique(data: SimulationInput):

    try:

        parametres = data.to_calculation_dict()

        resultats = parametric_study(parametres)

        return {
            "success": True,
            "message": "Étude paramétrique réalisée.",
            **resultats
        }

    except (ValueError, ZeroDivisionError) as erreur:

        raise HTTPException(
            status_code=400,
            detail=str(erreur)
        )
