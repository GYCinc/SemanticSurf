const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  getProfiles: () => ipcRenderer.invoke('get-profiles'),
  saveProfiles: (profiles) => ipcRenderer.send('save-profiles', profiles),
  getConfig: () => ipcRenderer.invoke('get-config'),
  toggleAlwaysOnTop: () => ipcRenderer.send('toggle-always-on-top'),
  saveCardToSanity: (cardData) => ipcRenderer.invoke('save-card-to-sanity', cardData), // Expose Sanity save
});
