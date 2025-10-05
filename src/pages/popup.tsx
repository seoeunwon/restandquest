import React from "react";
import "./popup.css";

type PopupProps = {
  message?: string;
  onClose: () => void;
};

const Popup: React.FC<PopupProps> = ({ onClose }) => {
  return (
    <div className="popups-overlay" onClick={onClose}>
      <div className="popups-content" onClick={(e) => e.stopPropagation()}>
        <p>explaination about the app</p>
        <button className="popups-close" onClick={onClose}>
          close
        </button>
      </div>
    </div>
  );
};

export default Popup;
