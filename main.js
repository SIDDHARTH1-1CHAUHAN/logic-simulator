const { app, BrowserWindow } = require("electron");
const path = require("path");

let mainWindow;

app.whenReady().then(() => {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true, // Allows Node.js modules in the frontend
        },
    });

    mainWindow.loadFile(path.join(__dirname, "index.html"));

    mainWindow.on("closed", () => {
        mainWindow = null;
    });
});

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
