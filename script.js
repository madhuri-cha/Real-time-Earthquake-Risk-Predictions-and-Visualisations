const btn = document.getElementById("btn");

// Add loading state to button
function setLoading(isLoading) {
    if (isLoading) {
        btn.innerHTML = '<div class="loading" style="width: 16px; height: 16px; margin: 0;"></div> Loading...';
        btn.disabled = true;
    } else {
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Search';
        btn.disabled = false;
    }
}

btn.addEventListener("click", async () => {
    const t = document.getElementById("time");
    let period = t.value;
    let cards = document.getElementById("cards");
    
    cards.innerHTML = '<div class="empty-state"><div class="loading"></div><p>Fetching earthquake data...</p></div>';
    setLoading(true);

    try {
        await fetch('https://real-time-earthquake-risk-predictions.onrender.com/period/', {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ time: period })
        });

        const ws = new WebSocket("wss://real-time-earthquake-risk-predictions.onrender.com/ws");
        
        ws.onmessage = (event) => {
            let data = JSON.parse(event.data);
            let length = data["place"].length;
            
            // Reset container
            cards.innerHTML = "";
            
            if (length === 0) {
                cards.innerHTML = '<div class="empty-state"><h2>No earthquake data found</h2><p>Try a different time period</p></div>';
                setLoading(false);
                return;
            }

            // Apply staggered animation to cards
            for (let i = 0; i < length; i++) {
                let tsunamiValue = data['tsunami'][i] ? data['tsunami'][i] : 'None';
                let riskClass = data['predictions'][i];
                
                // Create card with delay for animation
                setTimeout(() => {
                    let card = document.createElement('div');
                    card.className = 'card';
                    card.style.animationDelay = `${i * 0.1}s`;
                    
                    card.innerHTML = `
                        <h2>${data['place'][i]}</h2>
                        <p><strong>Magnitude:</strong> <span class="magnitude">${data['magnitude'][i]} ${data['magType'][i]}</span></p>
                        <p><strong>Details:</strong> ${data['title'][i]}</p>
                        <p><strong>Type:</strong> ${data['type'][i]}</p>
                        <p><strong>Coordinates:</strong> ${data['coordinates'][i]}</p>
                        <p><strong>Tsunami:</strong> <span class="tsunami">${tsunamiValue}</span></p>
                        <p><strong>Risk Level:</strong> <span class="risk ${riskClass}">${riskClass}</span></p>
                        <p><strong>More Info:</strong> <span><a href="${data['url'][i]}" target="_blank">USGS Data</a></span></p>
                        <p><strong>Detailed Report:</strong> <span><a href="${data['details'][i]}" target="_blank">View Report</a></span></p>
                    `;
                    
                    cards.appendChild(card);
                }, 10); // Small delay to ensure DOM has time to process
            }
            
            setLoading(false);
        };

        ws.onerror = (event) => {
            cards.innerHTML = '<div class="empty-state"><h2>No Data Available</h2><p>Please try a different time period.</p></div>';
            setLoading(false);
        };
        
        ws.onclose = () => {
            setLoading(false);
        };
    } catch (error) {
        cards.innerHTML = '<div class="empty-state"><h2>Connection Error</h2><p>Could not connect to the server. Please try again later.</p></div>';
        setLoading(false);
    }
});

// Initialize with empty state text
document.addEventListener('DOMContentLoaded', function() {
    let cards = document.getElementById("cards");
    if (cards.children.length === 0) {
        cards.innerHTML = '<div class="empty-state"><h2>Select a time period and click Search</h2><p>View real-time earthquake risk classifications around the world</p></div>';
    }
});