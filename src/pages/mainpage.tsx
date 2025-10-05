import React, { useState } from "react";
import { Play, Info, MessageSquare } from "lucide-react";
import "./mainpage.css";
import { locations } from "../jsonfile/locations";
import Popup from "./popup";
import ChatPopup from "./chatbot";

function App() {
  const [selectedCity, setSelectedCity] = useState("City 1");
  const [sliderValue, setSliderValue] = useState(0.0);
  const [showPopup, setShowPopup] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);
  const [time, setTime] = useState(6);
  const maxTime = 8;

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

  const handleInfoClick = () => {
    setShowPopup(true);
  };
  const handleChatbotClick = () => {
    setShowChatbot(true);
  };

  return (
    <div className="app-container">
      {/* Header */}
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
            <span className="temp">🌡 12°</span>
            <span className="weather">clear</span>
          </div>
        </div>

        <div className="time-bar-wrapper">
          <div className="time-bar-game">
            <div
              className="time-fill"
              style={{ width: `${(time / maxTime) * 100}%` }}
            />
          </div>
          <span className="time-text-side">time left: {time} hours</span>
        </div>
      </header>

      {/* Main Map */}
      <main className="main">
        <div
          className="map-placeholder"
          style={{ position: "relative", width: mapWidth, height: mapHeight }}
        >
          {locations
            .filter((loc) => loc.city === selectedCityNumber)
            .map((loc) => {
              const pos = getPosition(loc.latitude, loc.longitude);
              return (
                <div
                  key={loc.number}
                  style={{
                    position: "absolute",
                    width: 12,
                    height: 12,
                    borderRadius: "50%",
                    backgroundColor: "red",
                    left: pos.x - 6,
                    top: pos.y - 6,
                  }}
                  title={`number: ${loc.number}`}
                />
              );
            })}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="slider-section">
          <label htmlFor="slider" className="slider-label">
            Time estimation
          </label>
          <input
            id="slider"
            type="range"
            min={0.5}
            max={12.5}
            step={0.5}
            value={sliderValue}
            onChange={(e) => setSliderValue(parseFloat(e.target.value))}
            className="slider"
          />
          <p>🚙 {sliderValue} hours later</p>
        </div>

        <div className="action-buttons">
          <button className="action-button">
            <Play className="action-icon" />
          </button>
          <button className="action-button" onClick={handleChatbotClick}>
            <MessageSquare className="action-icon" />
          </button>
          <button className="action-button" onClick={handleInfoClick}>
            <Info className="action-icon" />
          </button>
        </div>
      </footer>

      {/* Popup */}
      {showChatbot && <ChatPopup onClose={() => setShowChatbot(false)} />}
      {showPopup && <Popup onClose={() => setShowPopup(false)} />}
    </div>
  );
}

export default App;
