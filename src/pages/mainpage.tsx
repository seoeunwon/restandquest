import React, { useState } from "react";
import { Coffee, Info, MessageSquare } from "lucide-react";
import "./mainpage.css";
import Popup from "./popup";
import ChatPopup from "./chatbot";
import { locations } from "../jsonfile/data";
import expectedEarnings from "../assets/expected_earnings_per_driver.json";

function App() {
  const [selectedCity, setSelectedCity] = useState("City 1");
  const [time, setTime] = useState(0);
  const [timeOffset, setTimeOffset] = useState(0);
  const [restTime, setRestTime] = useState(0);
  const [showPopup, setShowPopup] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);

  const maxTime = 4;
  const hpTime = 8;
  const dotSize = 20;
  const mapWidth = 350;
  const mapHeight = 300;
  const selectedCityNumber = parseInt(selectedCity.split(" ")[1]);

  const minLat = Math.min(...locations.map((l) => l.latitude));
  const maxLat = Math.max(...locations.map((l) => l.latitude));
  const minLng = Math.min(...locations.map((l) => l.longitude));
  const maxLng = Math.max(...locations.map((l) => l.longitude));

  const getPosition = (lat: number, lng: number) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * mapWidth;
    const y = mapHeight - ((lat - minLat) / (maxLat - minLat)) * mapHeight;
    return { x, y };
  };

  const handleInfoClick = () => setShowPopup(true);
  const handleChatbotClick = () => setShowChatbot(true);

  const handleSliderChange = (val: number) => {
    if (val >= maxTime) {
      setTime(0);
      setTimeOffset((prev) => (prev === 0 ? 4 : 0));
    } else {
      setTime(val);
    }
  };

  const handlePlayClick = () => {
    setRestTime((prev) => prev + 0.5);
  };

  const actualTime = time + timeOffset;

  const currentData = expectedEarnings.data.find(
    (row: any) =>
      row[0] === "clear" &&
      row[1] === selectedCityNumber &&
      row[2] === actualTime
  );

  const passengerCircles = locations
    .filter((loc) => loc.city === selectedCityNumber)
    .map((loc) => {
      const pos = getPosition(loc.latitude, loc.longitude);
      const value =
        currentData && loc.number >= 0 && loc.number <= 5
          ? Number(currentData[3 + loc.number])
          : 0;
      return { x: pos.x, y: pos.y, value, clusterNumber: loc.number };
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
          <div>
            <span className="day-indicator">2025.10.05(SUN)</span>
          </div>
          <div className="weather-info">
            <span className="temp">🌡 12°</span>
            <span className="weather">clear</span>
          </div>
        </div>

        <div className="time-bar-wrapper">
          <div className="time-bar-game">
            <div
              style={{
                width: `${((hpTime - actualTime + restTime) / hpTime) * 100}%`,
                height: "100%",
                backgroundColor: "green",
              }}
            />
          </div>
          <span className="time-text-side">
            time left: {Math.max(0, Math.round(hpTime - actualTime + restTime))}{" "}
            hours
          </span>
        </div>
      </header>

      <main className="main">
        <div
          className="map-placeholder"
          style={{ position: "relative", width: mapWidth, height: mapHeight }}
        >
          {passengerCircles.map((c, i) => {
            const v = c.value;
            let color = "white";
            if (v > 0 && v <= 4) color = "yellow";
            else if (v > 4 && v <= 8) color = "orange";
            else if (v > 8) color = "red";

            return (
              <div key={i}>
                <div
                  style={{
                    position: "absolute",
                    width: dotSize,
                    height: dotSize,
                    borderRadius: "50%",
                    backgroundColor: color,
                    left: c.x - dotSize / 2,
                    top: c.y - dotSize / 2,
                    border: "1px solid black",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: c.x - 11,
                    top: c.y - 28,
                    fontSize: "12px",
                    fontWeight: "bold",
                    color: "black",
                  }}
                >
                  {v > 0 ? v.toFixed(2) : ""}
                </div>
              </div>
            );
          })}
        </div>
      </main>

      <footer className="footer">
        <div className="slider-section">
          <label htmlFor="slider" className="slider-label">
            Time estimation
          </label>
          <input
            id="slider"
            type="range"
            min={0}
            max={maxTime}
            step={0.5}
            value={time}
            onChange={(e) => handleSliderChange(parseFloat(e.target.value))}
            className="slider"
          />
          <p>🚙 {actualTime} hours later</p>
        </div>

        <div className="action-buttons">
          <button className="action-button" onClick={handlePlayClick}>
            <Coffee className="action-icon" />
          </button>
          <button className="action-button" onClick={handleChatbotClick}>
            <MessageSquare className="action-icon" />
          </button>
          <button className="action-button" onClick={handleInfoClick}>
            <Info className="action-icon" />
          </button>
        </div>
      </footer>

      {showChatbot && <ChatPopup onClose={() => setShowChatbot(false)} />}
      {showPopup && <Popup onClose={() => setShowPopup(false)} />}
    </div>
  );
}

export default App;
