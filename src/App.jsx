import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import FirstPageLayout from './pages/FirstPageLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<FirstPageLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;