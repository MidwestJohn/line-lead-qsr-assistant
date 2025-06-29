import React from 'react';
import './SplashScreen.css';

/**
 * 🎨 Simple Splash Screen Component
 * 
 * Clean white loading screen with centered logo to mask startup process
 */
const SplashScreen = () => {
    return (
        <div className="splash-screen">
            <div className="splash-content">
                <img 
                    src="/LineLead_Logo.png" 
                    alt="Line Lead" 
                    className="splash-logo"
                />
            </div>
        </div>
    );
};

export default SplashScreen;