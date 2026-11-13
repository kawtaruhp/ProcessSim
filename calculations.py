
def simulate(data):

    # =====================================
    # CONSTANTES ET PARAMETRES
    # =====================================

    Cp = data["Cp"]
    lam = data["lambda"]

    m0 = data["m0"]
    x0 = data["x0"] / 100
    residus = data["residus"]

    mR = data["mR"]
    xR = data["xR"] / 100

    T2 = data["T2"]
    T3 = data["T3"]
    T5 = data["T5"]

    x4 = data["x4"] / 100

    # =====================================
    # 1. FILTRATION
    # =====================================

    m1 = m0 - residus

    if m1 <= 0:
        raise ValueError("Le débit après filtration doit être positif.")

    # Les solides solubles restent dans le jus
    x1 = (m0 * x0) / m1

    # =====================================
    # 2. MELANGE
    # =====================================

    m2 = m1 + mR

    x2 = (m1 * x1 + mR * xR) / m2

    # =====================================
    # 3. CHAUFFAGE
    # =====================================

    Q3 = m2 * Cp * (T3 - T2) / 3600

    # =====================================
    # 4. EVAPORATION
    # =====================================

    if x4 <= 0 or x4 > 1:
        raise ValueError("La concentration finale doit être entre 0 et 100 %.")

    if x4 < x2:
        raise ValueError(
            "La concentration finale doit être supérieure "
            "à la concentration après mélange."
        )

    # Débit final de jus concentré
    m4 = (m2 * x2) / x4

    # Débit d'eau évaporée
    mv = m2 - m4

    if mv < 0:
        raise ValueError("Le débit évaporé ne peut pas être négatif.")

    # Puissance thermique d'évaporation
    Q4 = mv * lam / 3600

    # =====================================
    # 5. REFROIDISSEMENT
    # =====================================

    Q5 = m4 * Cp * (T3 - T5) / 3600

    # =====================================
    # 6. BILAN DE MATIERE
    # =====================================

    # Matière soluble entrante
    matiere_soluble_entree = m0 * x0 + mR * xR

    # Matière soluble sortante
    matiere_soluble_sortie = m4 * x4

    # Eau entrante
    eau_entree = m0 * (1 - x0) + mR * (1 - xR)

    # Eau sortante : jus final + vapeur
    eau_sortie = m4 * (1 - x4) + mv

    # Erreurs de bilan
    erreur_soluble = (
        matiere_soluble_entree - matiere_soluble_sortie
    )

    erreur_eau = eau_entree - eau_sortie

    # Bilan global en incluant les particules insolubles
    entree_totale = m0 + mR
    sortie_totale = m4 + mv + residus

    erreur_globale = entree_totale - sortie_totale

    # =====================================
    # 7. RESULTATS
    # =====================================

    return {

        # Filtration
        "m1": round(m1, 2),
        "x1": round(x1 * 100, 2),

        # Mélange
        "m2": round(m2, 2),
        "x2": round(x2 * 100, 2),

        # Chauffage
        "Q3": round(Q3, 2),

        # Evaporation
        "m4": round(m4, 2),
        "mv": round(mv, 2),
        "Q4": round(Q4, 2),

        # Refroidissement
        "Q5": round(Q5, 2),

        # Bilan de matière
        "soluble_in": round(matiere_soluble_entree, 2),
        "soluble_out": round(matiere_soluble_sortie, 2),

        "water_in": round(eau_entree, 2),
        "water_out": round(eau_sortie, 2),

        "error_soluble": round(erreur_soluble, 6),
        "error_water": round(erreur_eau, 6),

        "total_in": round(entree_totale, 2),
        "total_out": round(sortie_totale, 2),
        "error_global": round(erreur_globale, 6)
    }


# =========================================
# 8. ETUDE PARAMETRIQUE
# =========================================

def parametric_study(data):

    # Etude de l'influence de la concentration finale
    concentration_results = []

    for concentration in range(40, 51, 2):

        params = data.copy()
        params["x4"] = concentration

        result = simulate(params)

        concentration_results.append({
            "x4": concentration,
            "mv": result["mv"],
            "m4": result["m4"],
            "Q4": result["Q4"]
        })

    # Etude de l'influence de la température
    temperature_results = []

    for temperature in range(80, 91, 2):

        params = data.copy()
        params["T3"] = temperature

        result = simulate(params)

        temperature_results.append({
            "T3": temperature,
            "Q3": result["Q3"]
        })

    # Résultats
    return {
        "concentration": concentration_results,
        "temperature": temperature_results
    }
