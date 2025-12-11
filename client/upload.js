console.log("JS Loaded");

const videoInput = document.getElementById("video-upload");
const uploadBtn = document.getElementById("upload-btn");
let selectedFile = null;

videoInput.addEventListener("change", (e) => {
  console.log("📌 File input changed:", e.target.files);
  if (e.target.files.length > 0) {
    selectedFile = e.target.files[0];
    console.log("📌 Selected File:", selectedFile);
    uploadBtn.disabled = false;
  } else {
    selectedFile = null;
    uploadBtn.disabled = true;
    console.log("❌ No file selected");
  }
});

uploadBtn.addEventListener("click", async (e) => {
  e.preventDefault(); // prevent form reload
  if (!selectedFile) {
    console.log("❌ No selected file");
    return alert("Select a file");
  }

  uploadBtn.innerText = "Processing...";
  uploadBtn.disabled = true;

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    console.log("🌐 Sending request to backend...");
    const res = await fetch("http://localhost:8000/api/detect-plate-video", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      console.error("❌ Backend error:", res.status);
      const errText = await res.text();
      console.error(errText);
      alert("Backend Error: " + res.status);
      uploadBtn.innerText = "Analyze Video";
      uploadBtn.disabled = false;
      return;
    }

    const data = await res.json();
    console.log("📥 Received JSON:", data);

    // Redirect to result page with session_id
    window.location.href = `result.html?session_id=${data.session_id}`;

  } catch (err) {
    console.error("🚨 Fetch Error:", err);
    alert("JS Error: " + err.message);
  } finally {
    uploadBtn.innerText = "Analyze Video";
    uploadBtn.disabled = false;
  }
});
