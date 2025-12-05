/*
This file is the launcher.
FIX: It now loads "viewer2.html" instead of "viewer.html".
FIX: It adds the security policy to fix the "endless spinner" bug.
*/

const { app, BrowserWindow, session, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const { sanityClient } = require("./sanityClient"); // Import Sanity Client

// Define the path for student profiles
const profilesPath = path.join(__dirname, "student_profiles.json");

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    backgroundColor: "#1a1a2e",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false, // Prevent freezing in background
    },
    frame: false,
    titleBarStyle: "hidden",
    alwaysOnTop: true, // Keep the window always on top
  });

  // --- FIX: Content Security Policy (Allows connection to ws://localhost:8765 and external scripts) ---
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [
          "default-src 'self' https://unpkg.com; img-src 'self' data:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' ws://localhost:8765",
        ],
      },
    });
  });
  // --- END FIX ---

  // --- CACHE CLEAR (Force Fresh Load) ---
  session.defaultSession.clearCache().then(() => {
    console.log("CLEARED ELECTRON CACHE");
  });

  // --- FIX: Load the correct file ---
  mainWindow.loadFile("viewer2.html");

  // Open the DevTools (developer console) automatically for debugging.
  // You can remove this line later by adding '//' in front of it.
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  // IPC handler for getting profiles
  ipcMain.handle("get-profiles", async () => {
    try {
      if (fs.existsSync(profilesPath)) {
        const data = fs.readFileSync(profilesPath, "utf8");
        return JSON.parse(data);
      }
      return {};
    } catch (error) {
      console.error("Failed to read profiles:", error);
      return {};
    }
  });

  // IPC handler for saving profiles
  ipcMain.on("save-profiles", (event, profiles) => {
    try {
      fs.writeFileSync(profilesPath, JSON.stringify(profiles, null, 2));
    } catch (error) {
      console.error("Failed to save profiles:", error);
    }
  });

  // IPC handler for getting config
  ipcMain.handle("get-config", async () => {
    try {
      const configPath = path.join(__dirname, "config.json");
      if (fs.existsSync(configPath)) {
        const data = fs.readFileSync(configPath, "utf8");
        return JSON.parse(data);
      }
      return {};
    } catch (error) {
      console.error("Failed to read config:", error);
      return {};
    }
  });

  // IPC handler for toggling "Always on Top"
  ipcMain.on("toggle-always-on-top", (event) => {
    const win = BrowserWindow.getFocusedWindow();
    if (win) {
      const isAlwaysOnTop = win.isAlwaysOnTop();
      win.setAlwaysOnTop(!isAlwaysOnTop);
      // Optional: Send status back if needed, or just let user verify visually
      console.log(`Always on Top: ${!isAlwaysOnTop}`);
    }
  });

  // --- SANITY IPC HANDLER ---
  ipcMain.handle("save-card-to-sanity", async (event, cardData) => {
    console.log("📤 Sending card to Sanity:", cardData);
    try {
      const result = await sanityClient.create({
        _type: 'analysisCard',
        ...cardData
      });
      console.log("✅ Saved to Sanity:", result._id);
      return { success: true, id: result._id };
    } catch (error) {
      console.error("❌ Sanity Save Error:", error);
      return { success: false, error: error.message };
    }
  });

  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", function () {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
