// import logo from './logo.svg';
// import './App.css';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;

import React, { useEffect } from 'react';
import axios from 'axios';

const App = () => {
    useEffect(() => {
        axios.get('http://localhost:5000/api/test') // Replace this with the valid backend endpoint
            .then(response => console.log(response.data))
            .catch(error => console.error('Error fetching data:', error));
    }, []);

    return (
        <div>
            <h1>Yeslove Frontend</h1>
            <p>Check the console for Flask API response one.</p>
        </div>
    );
};

export default App;
