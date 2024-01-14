import React from 'react';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SubscriptionForm from './SubscriptionForm';
import SubmissionPage from './SubmissionPage';

const theme = extendTheme({
  fonts: {
    heading: "'Poppins', sans-serif",
    body: "'Lato', sans-serif",
  },
  colors: {
    mistyRose: 'rgb(255, 228, 225)',
    pink: 'rgb(255, 194, 209)',
    cherryBlossomPink: 'rgb(255, 179, 198)',
    bakerMillerPink: 'rgba(255, 143, 171)',
    rosePompadour: 'rgba(251, 111, 146)',
  },
  styles: {
    global: {
      'input:focus': {
        boxShadow: 'none',
      },
    },
  },
});

const App = () => {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<SubscriptionForm />} />
          <Route path="/success" element={<SubmissionPage />} />
        </Routes>
      </Router>
    </ChakraProvider>
  );
};

export default App;
