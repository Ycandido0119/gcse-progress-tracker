// Dashboard Charts Initialization - RESPONSIVE VERSION
// Optimized for mobile, tablet, and desktop

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard charts script loaded');

    // Get chart canvases
    const weeklyCanvas = document.getElementById('weeklyStudyChart');
    const subjectCanvas = document.getElementById('subjectComparisonChart');
    const progressCanvas = document.getElementById('progressDonutChart');

    // Check if canvases exist
    if (!weeklyCanvas || !subjectCanvas || !progressCanvas) {
        console.error('One or more chart canvases not found');
        return;
    }

    console.log('All canvases found successfully!');

    // Helper function to detect screen size
    function isMobile() {
        return window.innerWidth < 576;
    }

    function isTablet() {
        return window.innerWidth >= 576 && window.innerWidth < 992;
    }

    // Get responsive font size
    function getFontSize() {
        if (isMobile()) return 10;
        if (isTablet()) return 11;
        return 12;
    }

    // Get raw data
    const weeklyDataRaw = weeklyCanvas.dataset.chartData;
    const subjectDataRaw = subjectCanvas.dataset.chartData;
    const progressDataRaw = progressCanvas.dataset.chartData;

    // Parse data
    let weeklyData, subjectData, progressData;
    
    try {
        weeklyData = JSON.parse(weeklyDataRaw);
        console.log('Parsed weekly data:', weeklyData);
    } catch (e) {
        console.error('Error parsing weekly data:', e);
        weeklyData = { labels: [], data: [] };
    }

    try {
        subjectData = JSON.parse(subjectDataRaw);
        console.log('Parsed subject data:', subjectData);
    } catch (e) {
        console.error('Error parsing subject data:', e);
        subjectData = { labels: [], data: [] };
    }

    try {
        progressData = JSON.parse(progressDataRaw);
        console.log('Parsed progress data:', progressData);
    } catch (e) {
        console.error('Error parsing progress data:', e);
        progressData = { labels: ['Completed', 'Remaining'], data: [0, 100] };
    }

    // Chart.js default configuration
    Chart.defaults.font.family = "'Inter', 'system-ui', '-apple-system', 'sans-serif'";
    Chart.defaults.color = '#6B7280';

    // Store chart instances for resize handling
    let weeklyChart, subjectChart, progressChart;

    // 1. Weekly Study Time Chart (Line Chart) - RESPONSIVE
    try {
        const weeklyCtx = weeklyCanvas.getContext('2d');
        
        weeklyChart = new Chart(weeklyCtx, {
            type: 'line',
            data: {
                labels: weeklyData.labels || [],
                datasets: [{
                    label: 'Hours Studied',
                    data: weeklyData.data || [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: isMobile() ? 2 : 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3B82F6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: isMobile() ? 3 : 5,
                    pointHoverRadius: isMobile() ? 5 : 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: isMobile() ? 1.2 : 2,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        padding: isMobile() ? 10 : 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {
                            size: getFontSize() + 1,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: getFontSize()
                        },
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
                            font: {
                                size: getFontSize()
                            },
                            callback: function(value) {
                                return value + 'h';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: getFontSize()
                            },
                            maxRotation: 0,
                            minRotation: 0
                        },
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

    // 2. Study by Subject Chart (Bar Chart) - RESPONSIVE WITH LABEL FIX
    try {
        const subjectCtx = subjectCanvas.getContext('2d');
        
        // Truncate labels on mobile
        const originalLabels = subjectData.labels || [];
        const displayLabels = originalLabels.map(label => {
            if (isMobile() && label.length > 9) {
                return label.substring(0, 9) + '...';
            }
            return label;
        });
        
        subjectChart = new Chart(subjectCtx, {
            type: 'bar',
            data: {
                labels: displayLabels,
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
                    borderRadius: isMobile() ? 4 : 8,
                    barThickness: isMobile() ? 35 : isTablet() ? 45 : 60,
                    maxBarThickness: 80
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: isMobile() ? 1 : isTablet() ? 1.3 : 1.5,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        padding: isMobile() ? 10 : 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {
                            size: getFontSize() + 1,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: getFontSize()
                        },
                        borderColor: '#3B82F6',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            // Show full label in tooltip
                            title: function(context) {
                                return originalLabels[context[0].dataIndex];
                            },
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
                            font: {
                                size: getFontSize()
                            },
                            callback: function(value) {
                                return value + 'h';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: getFontSize()
                            },
                            maxRotation: 0,
                            minRotation: 0
                        },
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

    // 3. Overall Progress Chart (Doughnut Chart) - RESPONSIVE
    try {
        const progressCtx = progressCanvas.getContext('2d');
        
        progressChart = new Chart(progressCtx, {
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
                maintainAspectRatio: true,
                aspectRatio: 1,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: isMobile() ? 12 : 20,
                            font: {
                                size: getFontSize()
                            },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: isMobile() ? 8 : 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        padding: isMobile() ? 10 : 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {
                            size: getFontSize() + 1,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: getFontSize()
                        },
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

    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Destroy and recreate charts on resize for better responsiveness
            if (weeklyChart) weeklyChart.destroy();
            if (subjectChart) subjectChart.destroy();
            if (progressChart) progressChart.destroy();
            
            // Recreate charts (this will re-run the initialization)
            location.reload(); // Simple solution for now
        }, 500);
    });

    console.log('Chart initialization complete!');
});