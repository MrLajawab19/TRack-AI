import React, { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import L from 'leaflet'

const FitBoundsOnData = ({ data }) => {
  const map = useMap()
  const hasFit = useRef(false)

  useEffect(() => {
    if (!data || hasFit.current) return
    try {
      const layer = new L.GeoJSON(data)
      const bounds = layer.getBounds()
      if (bounds && bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] })
        hasFit.current = true
      }
    } catch (e) {
      // no-op if bounds can't be determined
    }
  }, [data, map])

  return null
}

export default function RailwayMap() {
  const [geojson, setGeojson] = useState(null)

  useEffect(() => {
    fetch('/data/delhi-kanpur-railway.geojson')
      .then((r) => r.json())
      .then((d) => setGeojson(d))
      .catch((e) => console.error('Failed to load GeoJSON', e))
  }, [])

  const style = useMemo(() => ({ color: 'red', weight: 2 }), [])

  return (
    <MapContainer
      center={[27.2, 78.5]}
      zoom={7}
      scrollWheelZoom={true}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {geojson && <GeoJSON data={geojson} style={style} />}
      <FitBoundsOnData data={geojson} />
    </MapContainer>
  )
}
