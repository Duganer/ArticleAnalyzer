async function onSubmit(event) {
    event.preventDefault();

    const urls = document.getElementById("urls").value.split(",");
    const summaryType = document.getElementById("summary_type").value;
    const keywords = document.getElementById("keywords").value.split(",");
    const startDate = document.getElementById("start_date").value;
    const endDate = document.getElementById("end_date").value;

    let apiUrl = '';
    let requestData = {};

    if (startDate && endDate) {
        apiUrl = '/summarize_by_date';
        requestData = {
            start_date: startDate,
            end_date: endDate,
            keywords: keywords,
            summary_type: summaryType,
        };
    } else if (urls.length > 0 && urls[0] !== '') {
        apiUrl = '/summarize';
        requestData = {
            urls: urls,
            summary_type: summaryType,
            keywords: keywords,
        };
    } else {
        alert("Please provide either URLs or a date range.");
        return;
    }

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            const data = await response.json();
            processDataAndDisplayResults(data);
        } else {
            alert("Error occurred while fetching data. Please try again.");
        }
    } catch (error) {
        console.error("Error during fetch:", error);
        alert("Error occurred while fetching data. Please check the console for more information.");
    }
}

function processDataAndDisplayResults(response) {
    // Populate the table
    const tableBody = document.getElementById("resultsTableBody");
    tableBody.innerHTML = "";
    response.results.forEach(result => {
        const row = document.createElement("tr");
        const urlCell = document.createElement("td");
        urlCell.textContent = result.url;
        row.appendChild(urlCell);

        const scoreCell = document.createElement("td");
        scoreCell.textContent = result.score;
        row.appendChild(scoreCell);

        const weightCell = document.createElement("td");
        weightCell.textContent = result.weight;
        row.appendChild(weightCell);

        const sentimentWeightCell = document.createElement("td");
        sentimentWeightCell.textContent = result.sentiment_weight;
        row.appendChild(sentimentWeightCell);

        const weightedScoreCell = document.createElement("td");
        weightedScoreCell.textContent = result.weighted_score;
        row.appendChild(weightedScoreCell);

        const dateCell = document.createElement("td");
        dateCell.textContent = result.date;
        row.appendChild(dateCell);

        tableBody.appendChild(row);
    });

    // Display the histogram
    displayHistogram(response.grouped_summaries);
}

function displayHistogram(groupedSummaries) {
    const ctx = document.createElement('canvas');
    document.getElementById('histogram').innerHTML = ''; // Clear previous histogram
    document.getElementById('histogram').appendChild(ctx);

    const labels = Object.keys(groupedSummaries);
    const data = labels.map(label => groupedSummaries[label]);

    const colors = [
        'rgba(75, 192, 192, 0.2)', // color 1
        'rgba(255, 99, 132, 0.2)', // color 2
        'rgba(255, 206, 86, 0.2)', // color 3
    ];
    const borderColors = [
        'rgba(75, 192, 192, 1)', // color 1
        'rgba(255, 99, 132, 1)', // color 2
        'rgba(255, 206, 86, 1)', // color 3
    ];

    const backgroundColors = data.map((_, index) => colors[index % colors.length]);
    const borderColor = data.map((_, index) => borderColors[index % borderColors.length]);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Combined Weight Score',
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

document.getElementById("submit-btn").addEventListener("click", onSubmit);

