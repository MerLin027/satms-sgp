// Create traffic chart
document.addEventListener('DOMContentLoaded', function() {
    // Generate more realistic data for the chart
    const generateRandomData = () => {
        // Generate random data with slight variation around a base value
        const baseValues = { north: 10, south: 8, east: 12, west: 9 };
        const timePoints = 20;
        
        const result = {};
        
        for (const direction in baseValues) {
            result[direction] = Array(timePoints).fill(0).map(() => {
                // Random value within ±30% of base value
                const variation = baseValues[direction] * 0.3; // 30% variation
                return Math.max(1, Math.round(baseValues[direction] + (Math.random() * variation * 2) - variation));
            });
        }
        
        return result;
    };
    
    const randomData = generateRandomData();
    
    // Create traffic chart with more realistic data
    const trafficData = {
        labels: Array.from({length: 20}, (_, i) => `${20-i}m ago`).reverse(),
        datasets: [
            {
                label: 'North',
                data: randomData.north,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
            },
            {
                label: 'South',
                data: randomData.south,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
            },
            {
                label: 'East',
                data: randomData.east,
                borderColor: 'rgba(255, 206, 86, 1)',
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
            },
            {
                label: 'West',
                data: randomData.west,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }
        ]
    };

    const ctx = document.getElementById('traffic-chart').getContext('2d');
    const trafficChart = new Chart(ctx, {
        type: 'line',
        data: trafficData,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Vehicle Count'
                    }
                }
            }
        }
    });
    
    // Update metrics with some random data
    document.getElementById('avg-wait-time').textContent = `${(Math.random() * 10 + 8).toFixed(1)}s`;
    document.getElementById('max-wait-time').textContent = `${(Math.random() * 15 + 20).toFixed(1)}s`;
    document.getElementById('throughput').textContent = `${Math.round(Math.random() * 20 + 30)} veh/min`;
    document.getElementById('queue-length').textContent = `${Math.round(Math.random() * 10 + 10)} vehicles`;
    
    // Apply strategy button
    document.getElementById('apply-strategy').addEventListener('click', function() {
        const strategy = document.getElementById('strategy-select').value;
        alert(`Strategy changed to: ${strategy}`);
        // In a real implementation, this would call an API endpoint
    });
});
