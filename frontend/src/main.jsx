import React from 'react'
import { createRoot } from 'react-dom/client'
import RailwayMap from './components/RailwayMap.jsx'
import 'leaflet/dist/leaflet.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <div style={{height: '100vh', width: '100vw'}}>
      <RailwayMap />
    </div>
  </React.StrictMode>
)
