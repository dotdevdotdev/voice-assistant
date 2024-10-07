document.addEventListener("DOMContentLoaded", () => {
  console.log("Renderer process started - version XYZ");

  // DOM element references
  const microphoneSelect = document.getElementById("microphone-select");
  const startButton = document.getElementById("start-button");
  const stopButton = document.getElementById("stop-button");
  const outputDiv = document.getElementById("output");

  console.log("DOM elements initialized");

  // Function to check microphone access and populate the select element
  async function checkMicrophone() {
    console.log("Checking microphone access...");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log("Microphone access granted");

      // Stop the stream immediately as we don't need it running
      stream.getTracks().forEach((track) => track.stop());

      // Populate the microphone select element
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputDevices = devices.filter(
        (device) => device.kind === "audioinput"
      );

      audioInputDevices.forEach((device) => {
        const option = document.createElement("option");
        option.value = device.deviceId;
        option.text =
          device.label || `Microphone ${microphoneSelect.length + 1}`;
        microphoneSelect.appendChild(option);
      });

      console.log("Microphone select populated");
    } catch (error) {
      console.error("Error accessing microphone:", error);
      outputDiv.textContent =
        "Error: Microphone access denied. Please check your browser settings.";
    }
  }

  // Function to start voice recognition
  function startVoiceRecognition() {
    console.log("Starting voice recognition...");
    // Send a message to the main process
    window.electronAPI.send("toMain", "Start voice recognition");
    outputDiv.textContent = "Voice recognition started...";
  }

  // Function to stop voice recognition
  function stopVoiceRecognition() {
    console.log("Stopping voice recognition...");
    // Send a message to the main process
    window.electronAPI.send("toMain", "Stop voice recognition");
    outputDiv.textContent = "Voice recognition stopped.";
  }

  // Event listeners
  startButton.addEventListener("click", startVoiceRecognition);
  stopButton.addEventListener("click", stopVoiceRecognition);

  // Listen for messages from the main process
  window.electronAPI.receive("fromMain", (message) => {
    console.log("Received from main:", message);
    // Handle the message from the main process
  });

  // Initialize microphone check
  checkMicrophone();

  console.log("Renderer process initialization complete");
});
