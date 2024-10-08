document.addEventListener("DOMContentLoaded", () => {
  console.log("Renderer process started - version XYZ");

  // DOM element references
  const microphoneSelect = document.getElementById("microphone-select");
  const startButton = document.getElementById("start-button");
  const stopButton = document.getElementById("stop-button");
  const outputDiv = document.getElementById("output");
  const responseDiv = document.getElementById("response");
  const statusDiv = document.getElementById("status");

  console.log("DOM elements initialized");

  let recognition = null;

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

  function startVoiceRecognition() {
    console.log("Starting voice recognition...");
    outputDiv.textContent = "Voice recognition started...";

    if ("webkitSpeechRecognition" in window) {
      recognition = new webkitSpeechRecognition();
    } else if ("SpeechRecognition" in window) {
      recognition = new SpeechRecognition();
    } else {
      console.error("Speech recognition not supported");
      outputDiv.textContent =
        "Speech recognition not supported in this browser.";
      return;
    }

    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      console.log("Speech recognition started");
      statusDiv.textContent = "Listening...";
    };

    recognition.onresult = async (event) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      console.log("Recognized:", transcript);
      outputDiv.textContent = `Recognized: ${transcript}`;

      if (result.isFinal) {
        // Process the speech with OpenAI
        try {
          statusDiv.textContent = "Processing...";
          const response = await window.electronAPI.processSpeech(transcript);
          responseDiv.textContent = `Assistant: ${response}`;
        } catch (error) {
          console.error("Error processing speech:", error);
          responseDiv.textContent = "Error: Unable to process speech.";
        } finally {
          statusDiv.textContent = "Listening...";
        }
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      outputDiv.textContent = `Error: ${event.error}`;
      if (event.error === "network") {
        outputDiv.textContent += ". Please check your internet connection.";
      }
    };

    recognition.onend = () => {
      console.log("Speech recognition ended");
      statusDiv.textContent = "";
    };

    try {
      recognition.start();
    } catch (error) {
      console.error("Error starting speech recognition:", error);
      outputDiv.textContent = `Error starting speech recognition: ${error.message}`;
    }
  }

  function stopVoiceRecognition() {
    console.log("Stopping voice recognition...");
    if (recognition) {
      recognition.stop();
      recognition = null;
    }
    outputDiv.textContent = "Voice recognition stopped.";
    statusDiv.textContent = "";
  }

  // Event listeners
  startButton.addEventListener("click", startVoiceRecognition);
  stopButton.addEventListener("click", stopVoiceRecognition);

  // Initialize microphone check
  checkMicrophone();

  console.log("Renderer process initialization complete");

  // When making any network requests, use HTTPS
  function makeApiRequest(url) {
    return fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        console.error("Error making API request:", error);
        throw error;
      });
  }

  // Example usage:
  makeApiRequest("https://api.example.com/data")
    .then((data) => console.log(data))
    .catch((error) => console.error("API Error:", error));
});
