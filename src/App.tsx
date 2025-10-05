// App.tsx
import React, { useState, useEffect } from "react";
import { Play, Info, MessageSquare } from "lucide-react";
import Popup from "./popup";
import "./Appcontent.css";
import { locations, weatherdata } from "./jsonfile/locations";

// weatherdata 타입: [weather, hour, start, end, city]
type WeatherRow = [string, number, number, number, number];

function App() {
  const [selectedCity, setSelectedCity] = useState("City 1");
  const [sliderValue, setSliderValue] = useState(0.0);
  const [currentRows, setCurrentRows] = useState<WeatherRow[]>([]);
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const mapWidth = 350;
  const mapHeight = 300;

  const minLat = Math.min(...locations.map((l) => l.latitude));
  const maxLat = Math.max(...locations.map((l) => l.latitude));
  const minLng = Math.min(...locations.map((l) => l.longitude));
  const maxLng = Math.max(...locations.map((l) => l.longitude));

  const getPosition = (lat: number, lng: number) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * mapWidth;
    const y = mapHeight - ((lat - minLat) / (maxLat - minLat)) * mapHeight;
    return { x, y };
  };

  const selectedCityNumber = parseInt(selectedCity.split(" ")[1]);

  useEffect(() => {
    const rows = weatherdata.filter(
      (r) => r[4] === selectedCityNumber && r[1] === sliderValue
    ) as WeatherRow[];
    setCurrentRows(rows);
  }, [sliderValue, selectedCityNumber]);

  const startSet = new Set<number>();
  const endSet = new Set<number>();
  currentRows.forEach((row) => {
    const s = row[2];
    const e = row[3];
    if (s >= 0 && s < locations.length) startSet.add(s);
    if (e >= 0 && e < locations.length) endSet.add(e);
  });

  return (
    <div className="app-container">
      <header className="header">
        <div className="top-bar">
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="city-select"
          >
            <option>City 1</option>
            <option>City 2</option>
            <option>City 3</option>
            <option>City 4</option>
            <option>City 5</option>
          </select>
          <div className="weather-info">
            <span className="temp">🌡 10°</span>
            <span className="weather">
              {currentRows.length > 0 ? currentRows[0][0] : "-"}
            </span>
          </div>
        </div>
      </header>

      <main className="main">
        <div
          className="map-placeholder"
          style={{ position: "relative", width: mapWidth, height: mapHeight }}
        >
          {locations
            .filter((loc) => loc.city === selectedCityNumber)
            .map((loc) => {
              const pos = getPosition(loc.latitude, loc.longitude);
              const color = startSet.has(loc.number)
                ? "green"
                : endSet.has(loc.number)
                ? "blue"
                : "red";

              return (
                <div
                  key={loc.number}
                  style={{
                    position: "absolute",
                    width: 12,
                    height: 12,
                    borderRadius: "50%",
                    backgroundColor: color,
                    left: pos.x - 6,
                    top: pos.y - 6,
                  }}
                  title={`number: ${loc.number}`}
                />
              );
            })}

          <svg
            width={mapWidth}
            height={mapHeight}
            style={{ position: "absolute", top: 0, left: 0 }}
          >
            {currentRows.map((row, idx) => {
              const s = row[2];
              const e = row[3];
              const startLoc = locations.find(
                (l) => l.city === selectedCityNumber && l.number === s
              );
              const endLoc = locations.find(
                (l) => l.city === selectedCityNumber && l.number === e
              );
              if (!startLoc || !endLoc) return null;

              const startPos = getPosition(
                startLoc.latitude,
                startLoc.longitude
              );
              const endPos = getPosition(endLoc.latitude, endLoc.longitude);

              return (
                <line
                  key={idx}
                  x1={startPos.x}
                  y1={startPos.y}
                  x2={endPos.x}
                  y2={endPos.y}
                  stroke="orange"
                  strokeWidth={2}
                />
              );
            })}
          </svg>
        </div>
      </main>

      <footer className="footer">
        <div className="slider-section">
          <label htmlFor="slider" className="slider-label">
            time estimation
          </label>
          <input
            id="slider"
            type="range"
            min={0.5}
            max={12}
            step={0.5}
            value={sliderValue}
            onChange={(e) => setSliderValue(parseFloat(e.target.value))}
            className="slider"
          />
        </div>
        <div className="graph-section">
          <p>🚙 {sliderValue} hours later</p>
        </div>
        <div className="action-buttons">
          <button className="action-button">
            <Play className="action-icon" />
          </button>
          <button className="action-button">
            <MessageSquare className="action-icon" />
          </button>
          <button
            className="action-button"
            onClick={() => setIsPopupOpen(true)}
          >
            <Info className="action-icon" />
          </button>
        </div>
      </footer>

      {isPopupOpen && <Popup onClose={() => setIsPopupOpen(false)} />}
    </div>
  );
}

export default App;
