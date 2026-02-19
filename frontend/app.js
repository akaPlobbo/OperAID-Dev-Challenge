const state = {
    connected: false,
    data: new Map(),
    updateCount: 0,
    chart: null
};

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        state.connected = true;
        updateConnectionStatus();
        initializeChart();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received data:', data);
            
            const key = `${data.maschinenId}_${data.scrapIndex}`;
            state.data.set(key, data);
            state.updateCount++;
            
            renderDashboard();
            updateChart();
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        state.connected = false;
        updateConnectionStatus();
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        state.connected = false;
        updateConnectionStatus();
        setTimeout(connectWebSocket, 3000);
    };

    return ws;
}

/**
 * Update connection status display
 */
function updateConnectionStatus() {
    const dot = document.getElementById('connectionDot');
    const status = document.getElementById('connectionStatus');
    
    if (state.connected) {
        dot.className = 'status-dot connected';
        status.textContent = 'Verbunden';
    } else {
        dot.className = 'status-dot disconnected';
        status.textContent = 'Getrennt - Versuche erneut zu verbinden...';
    }
}

/**
 * Render dashboard cards
 */
function renderDashboard() {
    const dashboard = document.getElementById('dashboard');
    const updateCount = document.getElementById('updateCount');
    
    updateCount.textContent = state.updateCount;

    if (state.data.size === 0) {
        dashboard.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">⏳</div>
                <h2>Warte auf Daten...</h2>
                <p>Stelle sicher, dass MQTT Broker und Simulator laufen</p>
            </div>
        `;
        return;
    }

    const sortedData = Array.from(state.data.values()).sort((a, b) => {
        if (a.maschinenId !== b.maschinenId) {
            return a.maschinenId.localeCompare(b.maschinenId);
        }
        return a.scrapIndex - b.scrapIndex;
    });

    dashboard.innerHTML = sortedData.map(data => {
        const timestamp = new Date(data.timestamp);
        let formattedTime;
        
        if (isNaN(timestamp.getTime())) {
            formattedTime = 'Ungültige Zeit';
        } else {
            formattedTime = timestamp.toLocaleTimeString('de-DE', {
                timeZone: 'Europe/Berlin',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }

        return `
            <div class="card">
                <div class="card-header">
                    <span class="machine-id">${data.maschinenId}</span>
                    <span class="scrap-index">Index ${data.scrapIndex}</span>
                </div>
                <div class="metric">
                    <div class="metric-label">Summe (letzte 60s)</div>
                    <div class="metric-value sum">${data.sumLast60s.toFixed(1)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Durchschnitt (letzte 60s)</div>
                    <div class="metric-value avg">${data.avgLast60s.toFixed(2)}</div>
                </div>
                <div class="timestamp">
                    🕐 ${formattedTime}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Initialize Chart.js bar chart
 */
function initializeChart() {
    if (state.chart) {
        state.chart.destroy();
    }

    const ctx = document.getElementById('barChart').getContext('2d');
    state.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Summe (60s)',
                    data: [],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                },
                {
                    label: 'Durchschnitt (60s)',
                    data: [],
                    backgroundColor: 'rgba(34, 197, 94, 0.8)',
                    borderColor: 'rgba(34, 197, 94, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 750
            }
        }
    });
}

/**
 * Update chart with latest data
 */
function updateChart() {
    if (!state.chart) return;

    const machines = ['A1', 'B1', 'C1'];
    const indices = [1, 2, 3];
    
    const labels = [];
    const sumData = [];
    const avgData = [];

    machines.forEach(machine => {
        indices.forEach(index => {
            const key = `${machine}_${index}`;
            const label = `${machine}-Index${index}`;
            labels.push(label);
            
            if (state.data.has(key)) {
                const data = state.data.get(key);
                sumData.push(data.sumLast60s);
                avgData.push(data.avgLast60s);
            } else {
                sumData.push(0);
                avgData.push(0);
            }
        });
    });

    state.chart.data.labels = labels;
    state.chart.data.datasets[0].data = sumData;
    state.chart.data.datasets[1].data = avgData;
    state.chart.update('none');
}

/**
 * Initialize application
 */
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
});
