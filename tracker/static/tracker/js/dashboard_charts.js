// Dashboard Charts Initialization
// This file initializes all Chart.js charts on the dashboard

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard charts script loaded');

    // Get chart canvases
    const weeklyCanvas = document.getElementById('weeklyStudyChart');
    const subjectCanvas = document.getElementById('subjectComparisonChart');
    const progressCanvas = document.getElementById('progressDonutChart');

    // Check if canvases exist
    if (!weeklyCanvas) {
        console.error('Weekly chart canvas not found');
        return;
    }
    if (!subjectCanvas) {
        console.error('Subject chart canvas not found');
        return;
    }
    if (!progressCanvas) {
        console.error('Progress chart canvas not found');
        return;
    }

    console.log('All canvases found successfully!');

    // Get raw data
    const weeklyDataRaw = weeklyCanvas.dataset.chartData;
    const subjectDataRaw = subjectCanvas.dataset.chartData;
    const progressDataRaw = progressCanvas.dataset.chartData;

    console.log('Raw weekly data:', weeklyDataRaw);
    console.log('Raw subject data:', subjectDataRaw);
    console.log('Raw progress data:', progressDataRaw);

    // Parse data - Django passes valid JSON, just parse it directly
    let weeklyData, subjectData, progressData;
    
    try {
        weeklyData = JSON.parse(weeklyDataRaw);
        console.log('Parsed weekly data successfully:', weeklyData);
    } catch (e) {
        console.error('Error parsing weekly data:', e);
        weeklyData = { labels: [], data: [] };
    }

    try {
        subjectData = JSON.parse(subjectDataRaw);
        console.log('Parsed subject data successfully:', subjectData);
    } catch (e) {
        console.error('Error parsing subject data:', e);
        subjectData = { labels: [], data: [] };
    }

    try {
        progressData = JSON.parse(progressDataRaw);
        console.log('Parsed progress data successfully:', progressData);
    } catch (e) {
        console.error('Error parsing progress data:', e);
        progressData = { labels: ['Completed', 'Remaining'], data: [0, 100] };
    }

    // Verify data
    console.log('Weekly labels:', weeklyData.labels);
    console.log('Weekly data:', weeklyData.data);
    console.log('Subject labels:', subjectData.labels);
    console.log('Subject data:', subjectData.data);
    console.log('Progress data:', progressData);

    // Chart.js default configuration
    Chart.defaults.font.family = "'Inter', 'system-ui', '-apple-system', 'sans-serif'";
    Chart.defaults.color = '#6B7280';

    // 1. Weekly Study Time Chart (Line Chart)
    try {
        const weeklyCtx = weeklyCanvas.getContext('2d');
        
        console.log('Creating weekly chart with data:', {
            labels: weeklyData.labels,
            data: weeklyData.data
        });
        
        const weeklyChart = new Chart(weeklyCtx, {
            type: 'line',
            data: {
                labels: weeklyData.labels || [],
                datasets: [{
                    label: 'Hours Studied',
                    data: weeklyData.data || [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3B82F6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#3B82F6',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(1) + ' hours';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'h';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        console.log('Weekly chart created successfully');
    } catch (e) {
        console.error('Error creating weekly chart:', e);
    }

    // 2. Study by Subject Chart (Bar Chart)
    try {
        const subjectCtx = subjectCanvas.getContext('2d');
        
        console.log('Creating subject chart with data:', {
            labels: subjectData.labels,
            data: subjectData.data
        });
        
        const subjectChart = new Chart(subjectCtx, {
            type: 'bar',
            data: {
                labels: subjectData.labels || [],
                datasets: [{
                    label: 'Total Hours',
                    data: subjectData.data || [],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 146, 60, 0.8)'
                    ],
                    borderColor: [
                        'rgb(59, 130, 246)',
                        'rgb(139, 92, 246)',
                        'rgb(236, 72, 153)',
                        'rgb(34, 197, 94)',
                        'rgb(251, 146, 60)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#3B82F6',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(1) + ' hours';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'h';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        console.log('Subject chart created successfully');
    } catch (e) {
        console.error('Error creating subject chart:', e);
    }

    // 3. Overall Progress Chart (Doughnut Chart)
    try {
        const progressCtx = progressCanvas.getContext('2d');
        
        console.log('Creating progress chart with data:', progressData);
        
        const progressChart = new Chart(progressCtx, {
            type: 'doughnut',
            data: {
                labels: progressData.labels || ['Completed', 'Remaining'],
                datasets: [{
                    data: progressData.data || [0, 100],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(229, 231, 235, 0.8)'
                    ],
                    borderColor: [
                        'rgb(34, 197, 94)',
                        'rgb(229, 231, 235)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 13
                            },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#22C55E',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const data = progressData.data || [0, 100];
                                const total = data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                return context.label + ': ' + context.parsed + ' tasks (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
        console.log('Progress chart created successfully');
    } catch (e) {
        console.error('Error creating progress chart:', e);
    }

    console.log('Chart initialization complete!');
});