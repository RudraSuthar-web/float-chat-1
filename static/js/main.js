document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;

        appendUserMessage(question);
        userInput.value = '';
        showLoader();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            });

            const data = await response.json();
            hideLoader();
            appendBotMessage(data);

        } catch (error) {
            hideLoader();
            const errorData = {
                response_type: 'error',
                message: 'Failed to connect to the server. Please try again later.'
            };
            appendBotMessage(errorData);
            console.error('Error:', error);
        }
    });

    function showLoader() {
        const loaderBubble = `
            <div class="flex justify-start" id="loader">
                <div class="bot-bubble p-4 rounded-lg border border-slate-700">
                    <div class="loader"></div>
                </div>
            </div>`;
        chatHistory.insertAdjacentHTML('beforeend', loaderBubble);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function hideLoader() {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.remove();
        }
    }

    function appendUserMessage(message) {
        const bubbleHtml = `
            <div class="flex justify-end">
                <div class="user-bubble p-4 rounded-lg border border-slate-700">
                    <p class="text-white">${message}</p>
                </div>
            </div>`;
        chatHistory.insertAdjacentHTML('beforeend', bubbleHtml);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function appendBotMessage(data) {
        let contentHtml = '';
        let summaryHtml = data.summary ? `<p class="text-slate-400 mb-4">${data.summary}</p>` : '';
        
        // --- THIS IS THE MAIN FIX ---
        // A unique ID for the plot div is created here and used consistently.
        const plotId = `plot-${Date.now()}`; 

        switch (data.response_type) {
            case 'plot':
                contentHtml = `<div id="${plotId}" class="w-full h-96 bg-transparent"></div>`;
                break;
            case 'table':
                contentHtml = `<div class="overflow-x-auto">${data.table_html}</div>`;
                break;
            case 'message':
                summaryHtml = ''; // No summary for simple messages
                contentHtml = `<p class="text-white">${data.message}</p>`;
                break;
            case 'error':
                summaryHtml = ''; // No summary for errors
                contentHtml = `<p class="text-red-400 font-semibold">Error:</p><p class="text-red-400 whitespace-pre-wrap">${data.message}</p>`;
                break;
        }

        const botBubbleHtml = `
            <div class="flex justify-start">
                <div class="bot-bubble p-4 rounded-lg border border-slate-700 w-full">
                    ${summaryHtml}
                    ${contentHtml}
                </div>
            </div>`;
        
        chatHistory.insertAdjacentHTML('beforeend', botBubbleHtml);

        // If the response was a plot, find the div we just created and render the chart.
        if (data.response_type === 'plot') {
            const plotDiv = document.getElementById(plotId);
            if (plotDiv && data.chart) {
                try {
                    const chartData = JSON.parse(data.chart);
                    Plotly.newPlot(plotDiv, chartData.data, chartData.layout);
                } catch (e) {
                    plotDiv.innerText = "Error rendering chart.";
                    console.error("Failed to parse or render chart JSON:", e);
                }
            }
        }
        
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});