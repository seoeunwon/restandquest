import React, { useState } from "react";
import { Play, Info, MessageSquare } from "lucide-react";
import "./Appcontent.css";
import { locations } from "./jsonfile/locations";

function App() {
  const [selectedCity, setSelectedCity] = useState("City 1");

  const mapWidth = 350;
  const mapHeight = 300;

  const selectedCityNumber = parseInt(selectedCity.split(" ")[1]);

  // 지도 좌표를 화면 위치로 변환
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
    alert("팝업창 오픈");
  };

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
        </div>
      </header>

      <main className="main">
        <div
          className="map-placeholder"
          style={{ position: "relative", width: mapWidth, height: mapHeight }}
        >
          {/* 선택된 city의 위치에 점만 표시 */}
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

      <footer className="footer">
        <div className="action-buttons">
          <button className="action-button">
            <Play className="action-icon" />
          </button>
          <button className="action-button">
            <MessageSquare className="action-icon" />
          </button>
          <button className="action-button" onClick={handleInfoClick}>
            <Info className="action-icon" />
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
