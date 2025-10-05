import React from "react";
import "./firstpage.css";
import logo from "../assets/logo_1.png";
import { useNavigate } from "react-router-dom";

const FirstPage: React.FC = () => {
  const navigate = useNavigate();
  const handleStart = () => {
    navigate("/main");
  };

  return (
    <div className="firstpage-container">
      <div className="logo-wrapper">
        <img src={logo} alt="Logo" className="logo" />
      </div>

      <div className="controls">
        <button className="start-button" onClick={handleStart}>
          Start Journey
        </button>
      </div>
    </div>
  );
};

export default FirstPage;
