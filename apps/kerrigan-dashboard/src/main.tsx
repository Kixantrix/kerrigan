import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import { primeOsHomeDir } from "./lib/shims/os.js";

// Pre-fetch the OS home directory so os.homedir() returns the real value
// synchronously by the time any data-layer code runs (e.g. readProjects()).
// This is a no-op in the web preview build.
await primeOsHomeDir();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
