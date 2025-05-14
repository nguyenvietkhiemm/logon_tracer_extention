const API_URL = 'http://localhost:5000/clients';
const REFRESH_INTERVAL = 1000; 

async function fetchClients() {
    try {
        const response = await fetch(API_URL, {
            method: 'GET'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch client data');
        }
        const clientStates = await response.json();
        updateClientTable(clientStates);
        hideError();
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
}


function updateClientTable(clientStates) {
    const tableBody = document.getElementById('client-table-body');
    tableBody.innerHTML = ''; 

    for (const [clientName, pingCount] of Object.entries(clientStates)) {
        const row = document.createElement('tr');
        const isOnline = pingCount > 0;

        row.innerHTML = `
            <td>${clientName}</td>
            <td>${pingCount}/10</td>
            <td>${pingCount >= 10 ? 'Data requesting...' : 'No'}</td>
            <td class="${isOnline ? 'online' : 'offline'}">
                ${isOnline ? 'Online' : 'Offline'}
            </td>
        `;
        tableBody.appendChild(row);
    }
}

function showError(message) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}


function hideError() {
    const errorMessage = document.getElementById('error-message');
    errorMessage.classList.add('hidden');
}


function startPolling() {
    fetchClients();
    setInterval(fetchClients, REFRESH_INTERVAL);
}


document.addEventListener('DOMContentLoaded', startPolling);

document.getElementById('export-btn').addEventListener('click', () => {
    const status = document.getElementById('export-status');
    status.textContent = '⏳ Exporting...';
    status.className = 'status-text';

    fetch('http://localhost:5000/export')
        .then(response => {
            if (!response.ok) {
                throw new Error('Export failed');
            }
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return response.json().then(json => {
                    status.textContent = `✅ ${json.message || "Export done"}`;
                    status.classList.add('success');
                    return;
                });
            } else {
                return response.blob().then(blob => {
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'exported_data.zip';
                    a.click();
                    URL.revokeObjectURL(url);
                    status.textContent = '✅ Export successful';
                    status.classList.add('success');
                });
            }
        })
        .catch(error => {
            status.textContent = '❌ ' + error.message;
            status.classList.add('error');
        });
});
