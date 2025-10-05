import React from "react";
import "./popup.css";

type PopupProps = {
  message?: string;
  onClose: () => void;
};

const Popup: React.FC<PopupProps> = ({ onClose }) => {
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-content" onClick={(e) => e.stopPropagation()}>
        <p>explaination about the app</p>
        <button className="popup-close" onClick={onClose}>
          close
        </button>
      </div>
    </div>
  );
};

export default Popup;
