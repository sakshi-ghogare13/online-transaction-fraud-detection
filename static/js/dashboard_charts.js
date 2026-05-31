document.addEventListener("DOMContentLoaded", () => {

    if (typeof Chart === "undefined") {
        console.error("Chart.js is not loaded.");
        return;
    }

    const fraudChart = document.getElementById("fraudChart");

    if (fraudChart) {
        const fraud = Number(fraudChart.dataset.fraud) || 0;
        const legitimate = Number(fraudChart.dataset.legitimate) || 0;

        new Chart(fraudChart, {
            type: "doughnut",

            data: {
                labels: ["Fraud", "Legitimate"],

                datasets: [{
                    data: [fraud, legitimate],
                    backgroundColor: [
                        "rgba(255, 111, 145, 0.85)",
                        "rgba(62, 224, 143, 0.85)"
                    ],
                    borderColor: [
                        "rgba(255, 111, 145, 1)",
                        "rgba(62, 224, 143, 1)"
                    ],
                    borderWidth: 1
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#eef6ff"
                        }
                    }
                }
            }
        });
    }

    const trendChart = document.getElementById("trendChart");

    if (trendChart) {
        const labels = JSON.parse(trendChart.dataset.labels || "[]");
        const values = JSON.parse(trendChart.dataset.values || "[]");

        new Chart(trendChart, {
            type: "line",

            data: {
                labels: labels,

                datasets: [{
                    label: "Daily Transactions",
                    data: values,
                    fill: true,
                    tension: 0.4,
                    borderColor: "rgba(94, 220, 255, 1)",
                    backgroundColor: "rgba(94, 220, 255, 0.18)",
                    borderWidth: 3,
                    pointRadius: 4
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#eef6ff"
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            color: "#c9d6e3"
                        },
                        grid: {
                            color: "rgba(255,255,255,0.06)"
                        }
                    },

                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: "#c9d6e3",
                            precision: 0
                        },
                        grid: {
                            color: "rgba(255,255,255,0.06)"
                        }
                    }
                }
            }
        });
    }

});