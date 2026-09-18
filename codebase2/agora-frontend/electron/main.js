import { app, BrowserWindow, shell } from "electron";
const FRONTEND_URL = "http://localhost:3000";
function createWindow() {
  const window = new BrowserWindow({
    width: 1280, height: 860, minWidth: 400, minHeight: 600,
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true },
  });
  window.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://")) void shell.openExternal(url);
    return { action: "deny" };
  });
  window.webContents.on("will-navigate", (event, url) => {
    if (new URL(url).origin !== FRONTEND_URL) event.preventDefault();
  });
  window.loadURL(FRONTEND_URL).catch(() => {
    console.error("Hãy chạy npm run dev trước khi mở ứng dụng máy tính.");
    app.quit();
  });
}
app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
