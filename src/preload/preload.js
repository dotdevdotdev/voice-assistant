const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  send: (channel, data) => {
    let validChannels = ["toMain"];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  receive: (channel, func) => {
    let validChannels = ["fromMain"];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  },
  processSpeech: (speechData) =>
    ipcRenderer.invoke("process-speech", speechData),
});

// Expose a function to request microphone access
contextBridge.exposeInMainWorld("microphoneAccess", {
  request: () => {
    return navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        // Microphone access granted
        return true;
      })
      .catch((err) => {
        console.error("Error accessing microphone:", err);
        return false;
      });
  },
});
