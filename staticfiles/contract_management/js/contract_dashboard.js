document.addEventListener('DOMContentLoaded', function() {
    // Contract Type Chart
    var contractTypeCtx = document.getElementById('contractTypeChart');
    if (contractTypeCtx) {
        var contractTypeChart = new Chart(contractTypeCtx, {
            type: 'doughnut',
            data: {
                labels: contractTypeLabels,
                datasets: [{
                    data: contractTypeData,
                    backgroundColor: [
                        '#4f46e5', // Indigo-600
                        '#10b981', // Emerald-500
                        '#0ea5e9', // Sky-500
                        '#f59e0b', // Amber-500
                        '#ef4444', // Red-500
                        '#6b7280'  // Gray-500
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Contract Status Chart
    var contractStatusCtx = document.getElementById('contractStatusChart');
    if (contractStatusCtx) {
        var contractStatusChart = new Chart(contractStatusCtx, {
            type: 'bar',
            data: {
                labels: contractStatusLabels,
                datasets: [{
                    label: 'Contracts by Status',
                    data: contractStatusData,
                    backgroundColor: [
                        '#d1d5db', // Gray-300 (Draft)
                        '#fcd34d', // Amber-300 (Pending)
                        '#34d399', // Emerald-400 (Signed)
                        '#60a5fa', // Blue-400 (Executed)
                        '#f87171', // Red-400 (Terminated)
                        '#9ca3af'  // Gray-400 (Expired)
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
});