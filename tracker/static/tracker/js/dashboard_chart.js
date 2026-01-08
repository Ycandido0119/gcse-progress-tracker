/**
 * Dashboard Charts
 * Initializes and configures Chart.js visualizations for the analytics dashboard
 */

(function() {
    'use strict';

    // Chart color scheme
    const COLORS = {
        primary: '#3B82F6',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        gray: '#6B7280',
        lightGray: '#E5E7EB',
        purple: '#8B5CF6',
        teal: '#14B8A6'
    };

    // Chart.js default options
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = COLORS.gray;

    /**
     * Initialize Weekly Study Time Chart
     */
    function initWeeklyStudyChart() {
        const canvas = document.getElementById('weeklyStudyChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const chartData = JSON.parse(canvas.dataset.chartData || '{}');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Hours Studied',
                    data: chartData.data || [],
                    borderColor: COLORS.primary,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: COLORS.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
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
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + ' hours';
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
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    /**
     * Initialize Subject Comparison Chart
     */
    function initSubjectComparisonChart() {
        const canvas = document.getElementById('subjectComparisonChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const chartData = JSON.parse(canvas.dataset.chartData || '{}');

        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, COLORS.primary);
        gradient.addColorStop(1, COLORS.purple);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Study Hours',
                    data: chartData.data || [],
                    backgroundColor: gradient,
                    borderRadius: 8,
                    borderWidth: 0
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
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + ' hours total';
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
    }

    /**
     * Initialize Progress Donut Chart
     */
    function initProgressDonutChart() {
        const canvas = document.getElementById('progressDonutChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const chartData = JSON.parse(canvas.dataset.chartData || '{}');

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Remaining'],
                datasets: [{
                    data: [
                        chartData.completed || 0,
                        chartData.remaining || 100
                    ],
                    backgroundColor: [
                        COLORS.success,
                        COLORS.lightGray
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 13
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + percentage + '%';
                            }
                        }
                    }
                }
            },
            plugins: [{
                // Custom plugin to draw percentage in center
                id: 'centerText',
                beforeDraw: function(chart) {
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;
                    
                    ctx.restore();
                    
                    const completed = chart.config.data.datasets[0].data[0];
                    const total = chart.config.data.datasets[0].data.reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((completed / total) * 100).toFixed(0) : 0;
                    
                    const fontSize = (height / 100).toFixed(2);
                    ctx.font = "bold " + fontSize + "em sans-serif";
                    ctx.textBaseline = "middle";
                    ctx.fillStyle = COLORS.success;
                    
                    const text = percentage + "%";
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;
                    
                    ctx.fillText(text, textX, textY);
                    ctx.save();
                }
            }]
        });
    }

    /**
     * Animate metric cards on scroll
     */
    function animateMetricCards() {
        const cards = document.querySelectorAll('.metric-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1
        });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            observer.observe(card);
        });
    }

    /**
     * Initialize all charts
     */
    function initCharts() {
        initWeeklyStudyChart();
        initSubjectComparisonChart();
        initProgressDonutChart();
        animateMetricCards();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCharts);
    } else {
        initCharts();
    }

})();