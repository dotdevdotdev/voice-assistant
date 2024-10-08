const { app, BrowserWindow, session } = require("electron");
const path = require("path");
const https = require("https");
const fs = require("fs");
const { Configuration, OpenAIApi } = require("openai");
require("dotenv").config();

let mainWindow;

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
  httpAgent: new https.Agent({ keepAlive: true }),
});
const openai = new OpenAIApi(configuration);

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "../preload/preload.js"),
      enableRemoteModule: false,
      sandbox: false,
    },
  });

  // Accept self-signed certificate for localhost
  session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
    callback({ requestHeaders: { ...details.requestHeaders } });
  });

  win.loadURL("https://localhost:3000");

  // Open DevTools (optional)
  win.webContents.openDevTools();
}

app.whenReady().then(() => {
  // Allow self-signed certificates for localhost
  app.on(
    "certificate-error",
    (event, webContents, url, error, certificate, callback) => {
      if (url.startsWith("https://localhost:")) {
        event.preventDefault();
        callback(true);
      } else {
        callback(false);
      }
    }
  );

  createWindow();
});

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

let conversationHistory = [];

async function generateResponse(message) {
  try {
    conversationHistory.push({ role: "user", content: message });

    const completion = await openai.createChatCompletion({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: "You are a helpful voice assistant." },
        ...conversationHistory,
      ],
    });

    const response = completion.data.choices[0].message.content;
    conversationHistory.push({ role: "assistant", content: response });

    // Keep only the last 10 messages to manage token usage
    if (conversationHistory.length > 10) {
      conversationHistory = conversationHistory.slice(-10);
    }

    return response;
  } catch (error) {
    console.error("Error calling OpenAI API:", error);
    return "I'm sorry, I encountered an error processing your request.";
  }
}

ipcMain.handle("process-speech", async (event, speechData) => {
  console.log("Processing speech:", speechData);
  const response = await generateResponse(speechData);
  return response;
});
