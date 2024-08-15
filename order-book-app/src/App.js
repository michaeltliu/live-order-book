import logo from './logo.svg';
import './App.css';
import {useState} from 'react'

function LoginForm({setIsLoggedIn, setUserData}) {
  const [input, setInput] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (input.trim() !== "") {
      const response = await fetch(`http://127.0.0.1:5000/login?username=${input}`);
      const data = await response.json();
      console.log(data);
      setUserData(data);
      setIsLoggedIn(true);
    }
  }

  return (
    <header className="App-header">
      <form onSubmit={handleSubmit}>
        <input type="text" value={input} placeholder="Username" onChange={(e)=>setInput(e.target.value)}>
        </input>
        <button type="submit">Submit</button>
      </form>
    </header>
  )
}

function LoggedInView({setUserData, userData, setIsLoggedIn}) {
  function handleLogout() {
    setUserData('');
    setIsLoggedIn(false);
  }

  return (
    <header className="App-header">
      <p>{userData.username}</p>
      <p>{userData.user_id}</p>
      <p>{userData.cash}</p>
      <p>{userData.position}</p>
      {userData.orders}
      {userData.trades}
      <button onClick={handleLogout}>Logout</button>
    </header>
  )
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState('');

  return (
    <div className="App">
      {
        isLoggedIn ? (
          <LoggedInView setIsLoggedIn={setIsLoggedIn} setUserData={setUserData} userData={userData}/>
        ) : (
          <LoginForm setIsLoggedIn={setIsLoggedIn} setUserData={setUserData}/>
        )
      }
    </div>
  );
}

export default App;
