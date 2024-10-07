const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "../preload/preload.js"),
      // Add these lines to enable microphone access
      enableRemoteModule: false,
      sandbox: false,
    },
  });

  win.loadFile("public/index.html");

  // Handle IPC messages from renderer
  ipcMain.on("toMain", (event, message) => {
    console.log("Received in main:", message);
    // You can send a response back to the renderer if needed
    win.webContents.send("fromMain", "Message received in main process");
  });
}

app.whenReady().then(createWindow);

// ... rest of your main.js code ...

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
