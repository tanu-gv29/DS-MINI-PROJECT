document.addEventListener("DOMContentLoaded", () => {
    // Initialize page content
    populateJobRoles();
    checkLoginPopup();
});

// Check if the user is logged in and show the login popup if necessary
function checkLoginPopup() {
    if (!sessionStorage.getItem("isLoggedIn")) {
        showLoginPopup();
    }
}

// Show the login popup if the user is not logged in
function showLoginPopup() {
    const popup = document.getElementById("loginPopup");
    popup.style.visibility = "visible";
}

// Close the login popup
function closeLoginPopup() {
    const popup = document.getElementById("loginPopup");
    popup.style.visibility = "hidden";
}

// Redirect to the login page
function openLoginPage() {
    window.location.href = "login.html";
}

// Populate job roles from a JSON file (for now, dummy data is used)
function populateJobRoles() {
    fetch("job_roles.json")
        .then(response => response.json())
        .then(data => {
            window.jobRoles = data.jobRoles;
            displayJobRoles(window.jobRoles);
        })
        .catch(error => console.error("Error loading job roles:", error));
}

// Filter job roles based on user input
function filterJobRoles() {
    const input = document.getElementById("jobRoleInput").value.toLowerCase();
    const filteredRoles = window.jobRoles.filter(role => role.toLowerCase().includes(input));
    displayJobRoles(filteredRoles);
}

// Display filtered job roles in the dropdown
function displayJobRoles(jobRoles) {
    const dropdown = document.getElementById("jobRoleDropdown");
    dropdown.innerHTML = ""; // Clear previous options
    jobRoles.forEach(role => {
        const option = document.createElement("div");
        option.className = "dropdown-option";
        option.textContent = role;
        option.onclick = () => {
            document.getElementById("jobRoleInput").value = role;
            dropdown.innerHTML = ""; // Clear dropdown after selection
        };
        dropdown.appendChild(option);
    });
}

// Handle login form submission
document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (email && password) {
        sessionStorage.setItem("isLoggedIn", "true");
        alert("Login successful!");
        window.location.href = "index.html";
    } else {
        alert("Please enter valid credentials.");
    }
});

// Handle skill gap analysis form submission
document.getElementById("gapAnalysisForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById("resume");
    const file = fileInput.files[0];
    const jobRole = document.getElementById("jobRoleDropdown").value;

    if (!file || !jobRole) {
        alert("Please complete both fields.");
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_role", jobRole);

    try {
        const response = await fetch("YOUR_API_URL_HERE/skill-gap", { method: "POST", body: formData });
        const result = await response.json();
        document.getElementById("gapAnalysisResult").innerHTML = `
            <h3>Matched Skills:</h3><p>${result.matched_skills.join(", ")}</p>
            <h3>Missing Skills:</h3><p>${result.missing_skills.join(", ")}</p>
        `;
        window.location.href = "feedback.html";
    } catch (error) {
        console.error("Error:", error);
        alert("There was an error processing your resume.");
    }
});

// Handle job role recommendation form submission
document.getElementById("jobRecommendationForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById("resumeJobRec");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file.");
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);

    try {
        const response = await fetch("YOUR_API_URL_HERE/job-recommendation", { method: "POST", body: formData });
        const result = await response.json();
        document.getElementById("jobRecommendationResult").innerHTML = `
            <h3>Recommended Job Roles:</h3><p>${result.recommended_roles.join(", ")}</p>
        `;
        window.location.href = "feedback.html";
    } catch (error) {
        console.error("Error:", error);
        alert("There was an error fetching job role recommendations.");
    }
});

// Analyze Skills Function
async function handleAnalyzeSkills() {
    const fileInput = document.getElementById("resume");
    const jobRoleInput = document.getElementById("jobRoleInput");

    const file = fileInput.files[0];
    const jobRole = jobRoleInput.value.trim();

    // Basic validation
    if (!file) {
        alert("Please upload a resume file.");
        fileInput.focus();
        return;
    }
    if (!jobRole) {
        alert("Please select or input a job role.");
        jobRoleInput.focus();
        return;
    }

    // Prepare FormData for POST request
    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_role", jobRole);

    try {
        // Make the POST request to the backend
        const response = await fetch("http://localhost:5000/analyze_skills", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();

        // Update results dynamically
        document.getElementById("results").innerHTML = `
            <h2>Analyze Skills Results</h2>
            <h3>Matched Skills:</h3>
            <p>${result.matched_skills.join(", ")}</p>
            <h3>Missing Skills:</h3>
            <p>${result.missing_skills.join(", ")}</p>
            <h3>Visualization:</h3>
            <img src="data:image/png;base64,${result.visualization}" alt="Skills Visualization">
        `;
    } catch (error) {
        console.error(error);
        alert("Error analyzing skills. Please try again.");
    }
}

// Get Recommendations Function
async function handleGetRecommendations() {
    const fileInput = document.getElementById("jobResume");

    const file = fileInput.files[0];

    // Basic validation
    if (!file) {
        alert("Please upload a resume file.");
        fileInput.focus();
        return;
    }

    // Prepare FormData for POST request
    const formData = new FormData();
    formData.append("resume", file);

    try {
        // Make the POST request to the backend
        const response = await fetch("http://localhost:5000/get_recommendations", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();

        // Update results dynamically
        document.getElementById("results").innerHTML = `
            <h2>Job Recommendations</h2>
            <h3>Recommended Roles:</h3>
            <p>${result.recommended_roles.join(", ")}</p>
            <h3>Visualization:</h3>
            <img src="data:image/png;base64,${result.visualization}" alt="Recommendations Visualization">
        `;
    } catch (error) {
        console.error(error);
        alert("Error fetching recommendations. Please try again.");
    }
}
