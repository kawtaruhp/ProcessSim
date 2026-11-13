
const form = document.getElementById("simulationForm");
const results = document.getElementById("results");
const message = document.getElementById("message");
const balance = document.getElementById("balance");

let evaporationChart = null;
let heatingChart = null;
let powerChart = null;

// Récupération des paramètres
function getData() {
    return {
        m0: Number(document.getElementById("m0").value),
        x0: Number(document.getElementById("x0").value),
        residus: Number(document.getElementById("residus").value),
        mR: Number(document.getElementById("mR").value),
        xR: Number(document.getElementById("xR").value),
        Cp: Number(document.getElementById("Cp").value),
        T2: Number(document.getElementById("T2").value),
        T3: Number(document.getElementById("T3").value),
        x4: Number(document.getElementById("x4").value),
        lambda: Number(document.getElementById("lambda").value),
        T5: Number(document.getElementById("T5").value)
    };
}

// Création d'un graphique
function createChart(canvasId, oldChart, type, labels, datasets) {
    if (oldChart) {
        oldChart.destroy();
    }

    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        console.error("Canvas introuvable :", canvasId);
        return null;
    }

    return new Chart(canvas, {
        type,
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: "bottom"
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Affichage des résultats
function displayResults(result) {
    const labels = {
        m1: "Débit après filtration",
        x1: "Concentration après filtration",
        m2: "Débit après mélange",
        x2: "Concentration après mélange",
        Q3: "Puissance de chauffage",
        m4: "Débit final de jus",
        mv: "Débit de vapeur évaporée",
        Q4: "Puissance d'évaporation",
        Q5: "Puissance de refroidissement"
    };

    const units = {
        m1: "kg/h", x1: "%",
        m2: "kg/h", x2: "%",
        Q3: "kW", m4: "kg/h",
        mv: "kg/h", Q4: "kW", Q5: "kW"
    };

    results.innerHTML = "";

    for (const key in labels) {
        const value = Number(result[key]);

        results.innerHTML += `
            <div class="result-card">
                <h4>${labels[key]}</h4>
                <p>${Number.isFinite(value) ? value.toFixed(2) : "N/A"} ${units[key]}</p>
            </div>
        `;
    }
}

// Affichage du bilan de matière
function displayBalance(result) {
    if (!balance) return;

    balance.innerHTML = `
        <div class="result-card">
            <h4>Matière soluble entrante</h4>
            <p>${Number(result.soluble_in).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Matière soluble sortante</h4>
            <p>${Number(result.soluble_out).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Eau entrante</h4>
            <p>${Number(result.water_in).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Eau sortante</h4>
            <p>${Number(result.water_out).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Entrée totale</h4>
            <p>${Number(result.total_in).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Sortie totale</h4>
            <p>${Number(result.total_out).toFixed(2)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Erreur bilan soluble</h4>
            <p>${Number(result.error_soluble).toFixed(6)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Erreur bilan eau</h4>
            <p>${Number(result.error_water).toFixed(6)} kg/h</p>
        </div>
        <div class="result-card">
            <h4>Erreur bilan global</h4>
            <p>${Number(result.error_global).toFixed(6)} kg/h</p>
        </div>
    `;
}

// Lancement de la simulation
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    message.textContent = "Calcul en cours...";
    message.className = "";
    results.innerHTML = "";

    if (balance) balance.innerHTML = "";

    const data = getData();

    try {
        // 1. Simulation principale
        const response = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(
                responseData.detail || "Erreur de calcul"
            );
        }

        const result = responseData.results;

        if (!result) {
            throw new Error("Les résultats sont absents de la réponse API.");
        }

        displayResults(result);
        displayBalance(result);

        // 2. Étude paramétrique
        const paramResponse = await fetch("/api/parametric", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const param = await paramResponse.json();

        if (!paramResponse.ok) {
            throw new Error(
                param.detail || "Erreur étude paramétrique"
            );
        }

        // 3. Graphique : concentration et vapeur
        evaporationChart = createChart(
            "evaporationChart",
            evaporationChart,
            "line",
            param.concentration.map(item => item.x4 + "%"),
            [{
                label: "Vapeur évaporée (kg/h)",
                data: param.concentration.map(item => item.mv),
                borderWidth: 3,
                tension: 0.3
            }]
        );

        // 4. Graphique : température et chauffage
        heatingChart = createChart(
            "heatingChart",
            heatingChart,
            "line",
            param.temperature.map(item => item.T3 + "°C"),
            [{
                label: "Puissance de chauffage (kW)",
                data: param.temperature.map(item => item.Q3),
                borderWidth: 3,
                tension: 0.3
            }]
        );

        // 5. Comparaison des puissances
        powerChart = createChart(
            "powerChart",
            powerChart,
            "bar",
            ["Chauffage", "Évaporation", "Refroidissement"],
            [{
                label: "Puissance (kW)",
                data: [result.Q3, result.Q4, result.Q5]
            }]
        );

        message.textContent =
            "Simulation et étude paramétrique réalisées avec succès !";

    } catch (error) {
        console.error(error);
        message.textContent = "Erreur : " + error.message;
        message.className = "error";
    }
});

// =====================================
// EXPORTATION DU RAPPORT PDF
// =====================================

const pdfButton = document.getElementById("pdfButton");

if (pdfButton) {

    pdfButton.addEventListener("click", async function () {

        const data = getData();

        pdfButton.disabled = true;
        pdfButton.textContent = "Génération du PDF...";

        try {

            const response = await fetch("/api/export-pdf", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {

                const error = await response.json();

                throw new Error(
                    error.detail || "Erreur lors de la génération du PDF"
                );
            }

            // Récupération du fichier PDF
            const blob = await response.blob();

            // Création du lien de téléchargement
            const url = window.URL.createObjectURL(blob);

            const link = document.createElement("a");

            link.href = url;
            link.download = "ProcessSim_Rapport.pdf";

            document.body.appendChild(link);

            link.click();

            link.remove();

            window.URL.revokeObjectURL(url);

            message.textContent =
                "Rapport PDF téléchargé avec succès !";

            message.className = "";

        } catch (error) {

            console.error(error);

            message.textContent =
                "Erreur PDF : " + error.message;

            message.className = "error";

        } finally {

            pdfButton.disabled = false;

            pdfButton.textContent =
                "Télécharger le rapport PDF";
        }

    });

}
