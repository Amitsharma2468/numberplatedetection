console.log("JS Loaded")

const uploadSection = document.getElementById("upload-section")
const resultSection = document.getElementById("result-section")
const videoInput = document.getElementById("video-upload")
const uploadBtn = document.getElementById("upload-btn")
const resultsDiv = document.getElementById("results")
const downloadBtn = document.getElementById("download-btn")
const newUploadBtn = document.getElementById("new-upload-btn")
const uploadForm = document.getElementById("upload-form")

let selectedFile = null

if (uploadForm) {
  uploadForm.addEventListener("submit", (e) => {
    e.preventDefault()
    e.stopPropagation()
    console.log("Form submit prevented")
    return false
  })
}

// File selection handler
videoInput.addEventListener("change", (e) => {
  console.log("File input changed:", e.target.files)
  if (e.target.files.length > 0) {
    selectedFile = e.target.files[0]
    console.log("Selected File:", selectedFile)
    uploadBtn.disabled = false
  } else {
    selectedFile = null
    uploadBtn.disabled = true
    console.log("No file selected")
  }
})

// Upload and analyze handler
uploadBtn.addEventListener("click", async (e) => {
  e.preventDefault()
  e.stopPropagation()
  e.stopImmediatePropagation()

  console.log("=== ANALYZE BUTTON CLICKED ===")

  if (!selectedFile) {
    console.log("No selected file")
    alert("Select a file")
    return false
  }

  console.log("Starting upload for:", selectedFile.name)
  uploadBtn.innerText = "Processing..."
  uploadBtn.disabled = true

  const formData = new FormData()
  formData.append("file", selectedFile)

  try {
    console.log("Sending request to backend...")
    const res = await fetch("http://localhost:8000/api/detect-plate-video", {
      method: "POST",
      body: formData,
    })

    console.log("Response received, status:", res.status)

    if (!res.ok) {
      console.error("Backend error:", res.status)
      const errText = await res.text()
      console.error(errText)
      alert("Backend Error: " + res.status)
      uploadBtn.innerText = "Analyze Video"
      uploadBtn.disabled = false
      return false
    }

    const data = await res.json()
    console.log("Received JSON:", data)

    await fetchResults(data.session_id)
  } catch (err) {
    console.error("Fetch Error:", err)
    alert("JS Error: " + err.message)
    uploadBtn.innerText = "Analyze Video"
    uploadBtn.disabled = false
  }

  return false
})

// Fetch and display results without page reload
async function fetchResults(session_id) {
  console.log("Fetching results for session:", session_id)

  try {
    const res = await fetch(`http://localhost:8000/api/get-video-info/${session_id}`)
    if (!res.ok) {
      console.error("Fetch failed:", res.status)
      resultsDiv.innerText = "Failed to get results"
      showResultSection()
      return
    }

    const data = await res.json()
    console.log("Result JSON:", data)

    // Populate results
    resultsDiv.innerHTML = ""
    if (data.cars && data.cars.length > 0) {
      data.cars.forEach((car) => {
        const div = document.createElement("div")
        div.innerText = `Car ${car.car_id}: ${car.plate}`
        resultsDiv.appendChild(div)
      })
    } else {
      resultsDiv.innerText = "No plates detected"
    }

    // Set download link
    downloadBtn.href = `http://localhost:8000/download-video/${session_id}`

    // Show result section, hide upload section
    showResultSection()
  } catch (err) {
    console.error("Error fetching results:", err)
    resultsDiv.innerText = "Error fetching results"
    showResultSection()
  }
}

function showResultSection() {
  console.log("Showing result section")
  uploadSection.style.display = "none"
  resultSection.style.display = "block"
}

function showUploadSection() {
  console.log("Showing upload section")
  resultSection.style.display = "none"
  uploadSection.style.display = "block"
  uploadBtn.innerText = "Analyze Video"
  uploadBtn.disabled = true
  videoInput.value = ""
  selectedFile = null
}

// New upload button handler
newUploadBtn.addEventListener("click", () => {
  console.log("Starting new upload")
  showUploadSection()
})
