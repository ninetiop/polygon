async function uploadFile() {
    const fileInput = document.getElementById("csv-file");
    const file = fileInput.files[0];

    if (!file) {
        displayServerResponse("Please select a CSV file.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("csv_file", file);

    try {
        const response = await fetch("http://localhost:8080/upload", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            displayServerResponse(`CSV file uploaded successfully! Polygon ID: ${data.id}`, "success");

            // ✅ Automatically update the ID input field
            document.getElementById("polygon-id").value = data.id;
        } else {
            displayServerResponse(data.detail || "An error occurred while uploading the file.", "error");
        }
    } catch (error) {
        displayServerResponse("Server connection error.", "error");
    }
}

async function loadPolygon() {
    const polygonIdInput = document.getElementById("polygon-id");
    const polygonId = polygonIdInput.value;

    if (!polygonId) {
        displayServerResponse("Please enter a polygon ID.", "error");
        return;
    }

    try {
        // Adjust URL to use parameterized route: "/polygon/{id}"
        const response = await fetch(`http://localhost:8080/polygon/${polygonId}`);
        
        if (response.ok) {
            const imgUrl = URL.createObjectURL(await response.blob());
            document.getElementById("polygon-img").src = imgUrl;
            displayServerResponse("Polygon retrieved successfully!", "success");
        } else {
            const data = await response.json();
            displayServerResponse(data.detail || "The polygon could not be retrieved.", "error");
        }
    } catch (error) {
        displayServerResponse("Server connection error.", "error");
    }
}

function displayServerResponse(message, type) {
    const serverResponseDiv = document.getElementById("server-response");
    
    serverResponseDiv.textContent = message;
    serverResponseDiv.className = "server-response"; // Reset previous classes
    serverResponseDiv.classList.add(type);  // Add 'success' or 'error' class

    serverResponseDiv.style.display = "block";  // Show message
}
