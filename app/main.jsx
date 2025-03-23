

import React from "react";
import ReactDOM from "react-dom/client";  // ✅ Updated import
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));  // ✅ React 18+ compatible
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
