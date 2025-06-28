import React, { useState, useEffect } from 'react';
import { Keyboard, X } from 'lucide-react';
import './PDFKeyboardHelp.css';

const PDFKeyboardHelp = ({ isVisible, onClose }) => {
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setShowHelp(true);
    } else {
      setShowHelp(false);
    }
  }, [isVisible]);

  const shortcuts = [
    {
      category: 'Navigation',
      shortcuts: [
        { keys: ['←', '→'], description: 'Navigate pages' },
        { keys: ['Home'], description: 'Go to first page' },
        { keys: ['End'], description: 'Go to last page' },
      ]
    },
    {
      category: 'Zoom',
      shortcuts: [
        { keys: ['+', '='], description: 'Zoom in' },
        { keys: ['-'], description: 'Zoom out' },
        { keys: ['0'], description: 'Reset zoom' },
      ]
    },
    {
      category: 'Controls',
      shortcuts: [
        { keys: ['ESC'], description: 'Close PDF preview' },
        { keys: ['F'], description: 'Toggle fullscreen' },
        { keys: ['D'], description: 'Download PDF' },
        { keys: ['?'], description: 'Show this help' },
      ]
    },
    {
      category: 'Accessibility',
      shortcuts: [
        { keys: ['Tab'], description: 'Navigate controls' },
        { keys: ['Enter'], description: 'Activate button' },
        { keys: ['Space'], description: 'Activate button' },
      ]
    }
  ];

  if (!showHelp) return null;

  return (
    <div className="pdf-keyboard-help-overlay" onClick={onClose}>
      <div 
        className="pdf-keyboard-help-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="keyboard-help-title"
      >
        <div className="pdf-keyboard-help-header">
          <div className="pdf-keyboard-help-title">
            <Keyboard className="keyboard-icon" aria-hidden="true" />
            <h3 id="keyboard-help-title">Keyboard Shortcuts</h3>
          </div>
          <button 
            onClick={onClose}
            className="pdf-keyboard-help-close"
            aria-label="Close keyboard shortcuts help"
          >
            <X className="close-icon" aria-hidden="true" />
          </button>
        </div>

        <div className="pdf-keyboard-help-content">
          {shortcuts.map((category, index) => (
            <div key={index} className="pdf-keyboard-category">
              <h4 className="pdf-keyboard-category-title">{category.category}</h4>
              <div className="pdf-keyboard-shortcuts">
                {category.shortcuts.map((shortcut, shortcutIndex) => (
                  <div key={shortcutIndex} className="pdf-keyboard-shortcut">
                    <div className="pdf-keyboard-keys">
                      {shortcut.keys.map((key, keyIndex) => (
                        <React.Fragment key={keyIndex}>
                          <kbd className="pdf-keyboard-key">{key}</kbd>
                          {keyIndex < shortcut.keys.length - 1 && (
                            <span className="pdf-keyboard-or">or</span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                    <span className="pdf-keyboard-description">
                      {shortcut.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="pdf-keyboard-help-footer">
          <p className="pdf-keyboard-help-note">
            Press <kbd className="pdf-keyboard-key">?</kbd> anytime to show this help
          </p>
        </div>
      </div>
    </div>
  );
};

export default PDFKeyboardHelp;