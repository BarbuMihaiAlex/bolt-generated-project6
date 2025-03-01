CTFd._internal.challenge.data = undefined;
CTFd._internal.challenge.renderer = null;

// Format the connection information based on the protocol
function formatConnectionInfo(hostname, port, description) {
    if (hostname.startsWith('http')) {
        // For web services, create a clickable link
        return `<a href="${hostname}:${port}" target="_blank">${description}: ${hostname}:${port}</a>`;
    } else {
        // For other services, show as text with copy button
        const connectionString = `${hostname} ${port}`;
        return `
            <div class="d-flex align-items-center justify-content-center">
                <span class="mr-2">${description}: ${connectionString}</span>
                <button class="btn btn-sm btn-secondary ml-2" onclick="copyToClipboard('${connectionString}')">
                    <i class="fas fa-copy"></i>
                </button>
            </div>`;
    }
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        CTFd.ui.ezq.notify({
            title: 'Copied!',
            message: 'Connection info copied to clipboard',
            type: 'success'
        });
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Display port information in the UI
function displayPortInfo(hostname, ports, descriptions) {
    const portsContainer = document.getElementById('container-ports-info');
    portsContainer.innerHTML = '<h6 class="mb-3">Connection Information:</h6>';

    Object.entries(ports).forEach(([containerPort, hostPort]) => {
        const description = descriptions[containerPort] || `Port ${containerPort}`;
        const connectionInfo = formatConnectionInfo(hostname, hostPort, description);
        
        portsContainer.innerHTML += `
            <div class="port-info mb-2">
                ${connectionInfo}
            </div>`;
    });
}

function container_request(challenge_id) {
    var path = "/containers/api/request";
    var requestButton = document.getElementById("container-request-btn");
    var requestResult = document.getElementById("container-request-result");
    var containerExpires = document.getElementById("container-expires");
    var containerExpiresTime = document.getElementById("container-expires-time");
    var requestError = document.getElementById("container-request-error");

    requestButton.setAttribute("disabled", "disabled");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("CSRF-Token", init.csrfNonce);
    xhr.send(JSON.stringify({ chal_id: challenge_id }));

    xhr.onload = function () {
        var data = JSON.parse(this.responseText);
        if (data.error !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.error;
            requestButton.removeAttribute("disabled");
        } else if (data.message !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.message;
            requestButton.removeAttribute("disabled");
        } else {
            requestError.style.display = "none";
            requestError.firstElementChild.innerHTML = "";
            requestButton.parentNode.removeChild(requestButton);
            
            // Display port information
            displayPortInfo(data.hostname, data.ports, data.port_descriptions);
            
            containerExpires.innerHTML = Math.ceil((new Date(data.expires * 1000) - new Date()) / 1000 / 60);
            containerExpiresTime.style.display = "";
            requestResult.style.display = "";
        }
        console.log(data);
    };
}

function container_running(challenge_id) {
    var path = "/containers/api/running";
    var requestButton = document.getElementById("container-request-btn");
    var requestError = document.getElementById("container-request-error");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("CSRF-Token", init.csrfNonce);
    xhr.send(JSON.stringify({ chal_id: challenge_id }));

    xhr.onload = function () {
        var data = JSON.parse(this.responseText);
        if (data.error !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.error;
            requestButton.removeAttribute("disabled");
        } else if (data.message !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.message;
            requestButton.removeAttribute("disabled");
        } else if (data && data.status === "already_running" && data.container_id == challenge_id) {
            container_request(challenge_id);
        }
        console.log(data);
    };
}

function container_renew(challenge_id) {
    var path = "/containers/api/renew";
    var renewButton = document.getElementById("container-renew-btn");
    var requestResult = document.getElementById("container-request-result");
    var containerExpires = document.getElementById("container-expires");
    var requestError = document.getElementById("container-request-error");

    renewButton.setAttribute("disabled", "disabled");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("CSRF-Token", init.csrfNonce);
    xhr.send(JSON.stringify({ chal_id: challenge_id }));

    xhr.onload = function () {
        var data = JSON.parse(this.responseText);
        if (data.error !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.error;
            renewButton.removeAttribute("disabled");
        } else if (data.message !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.message;
            renewButton.removeAttribute("disabled");
        } else {
            requestError.style.display = "none";
            requestResult.style.display = "";
            containerExpires.innerHTML = Math.ceil((new Date(data.expires * 1000) - new Date()) / 1000 / 60);
            renewButton.removeAttribute("disabled");
        }
        console.log(data);
    };
}

function container_stop(challenge_id) {
    var path = "/containers/api/stop";
    var stopButton = document.getElementById("container-stop-btn");
    var requestResult = document.getElementById("container-request-result");
    var requestError = document.getElementById("container-request-error");
    var containerExpiresTime = document.getElementById("container-expires-time");

    stopButton.setAttribute("disabled", "disabled");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("CSRF-Token", init.csrfNonce);
    xhr.send(JSON.stringify({ chal_id: challenge_id }));

    xhr.onload = function () {
        var data = JSON.parse(this.responseText);
        if (data.error !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.error;
            stopButton.removeAttribute("disabled");
        } else if (data.message !== undefined) {
            requestError.style.display = "";
            requestError.firstElementChild.innerHTML = data.message;
            stopButton.removeAttribute("disabled");
        } else {
            requestError.style.display = "none";
            requestResult.innerHTML = "Container stopped. <br>Reopen this challenge to start another.";
            containerExpiresTime.style.display = "none";
        }
        console.log(data);
    };
}
