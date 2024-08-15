import logo from './logo.svg';
import './App.css';
import {useState} from 'react'

function App() {
  const [responseMessage, setResponseMessage] = useState('');
  const [input, setInput] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (input.trim() !== "") {
      const response = await fetch(`http://127.0.0.1:5000/create-user?username=${input}`);
      const data = await response.text();
      setResponseMessage(data);
    }
  }
  
  return (
    <div className="App">
      
        <form onSubmit={handleSubmit}>
          <input type="text" value={input} placeholder="Username" onChange={(e)=>setInput(e.target.value)}>
          </input>
          <button type="submit">Submit</button>
        </form>
        {responseMessage}
      
    </div>
  );
}

export default App;
