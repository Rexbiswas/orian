import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import FirstPageLayout from './pages/FirstPageLayout';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<FirstPageLayout />} />
      </Routes>
    </HashRouter>
  );
}

export default App;