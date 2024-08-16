import logo from './logo.svg';
import './App.css';
import {useState, useEffect} from 'react'
import Plot from 'react-plotly.js'

async function requestUserData(user_id, setUserData) {
  const response = await fetch(`http://127.0.0.1:5000/user-data/${user_id}`);
  const data = await response.json();
  console.log(data)
  setUserData(data);
  console.log('done');
}

async function requestPriceHistory(setPriceData) {
  const response = await fetch("http://127.0.0.1:5000/price-history");
  const data = await response.json();
  setPriceData(data);
}

function LoginForm({setIsLoggedIn, setUserData}) {
  const [input, setInput] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (input.trim() !== "") {
      const response = await fetch(`http://127.0.0.1:5000/login/${input}`);
      const user_id = await response.text();
      console.log(user_id)
      await requestUserData(user_id, setUserData);
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

function BuyForm({user_id, setUserData}) {
  const [limitInput, setLimitInput] = useState('');
  const [quantityInput, setQuantityInput] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (limitInput.trim() !== "" && quantityInput.trim() !== "") {
      const response = await fetch(`http://127.0.0.1:5000/buy/limit/${limitInput}/quantity/${quantityInput}/user_id/${user_id}`);
      const data = await response.text();
      setMessage(data);
      await requestUserData(user_id, setUserData)
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <input type="text" value={limitInput} name="limit" 
        placeholder="Limit Price" onChange={(e)=>setLimitInput(e.target.value)}/><br/>
        <input type="text" value={quantityInput} name="quantity" 
        placeholder="Quantity" onChange={(e)=>setQuantityInput(e.target.value)} /><br/>
        <button type="submit">Buy</button>
      </form>
      {message}
    </>
  )
}

function SellForm({user_id, setUserData}) {
  const [limitInput, setLimitInput] = useState('');
  const [quantityInput, setQuantityInput] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (limitInput.trim() !== "" && quantityInput.trim() !== "") {
      const response = await fetch(`http://127.0.0.1:5000/sell/limit/${limitInput}/quantity/${quantityInput}/user_id/${user_id}`);
      const data = await response.text();
      setMessage(data);
      await requestUserData(user_id, setUserData)
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <input type="text" value={limitInput} name="limit" 
        placeholder="Limit Price" onChange={(e)=>setLimitInput(e.target.value)}/><br/>
        <input type="text" value={quantityInput} name="quantity" 
        placeholder="Quantity" onChange={(e)=>setQuantityInput(e.target.value)} /><br/>
        <button type="submit">Sell</button>
      </form>
      {message}
    </>
  )
}

function UserDataPanel({setUserData, userData, setIsLoggedIn}) {
  useEffect(() => {
    const interval = setInterval(() => {
      requestUserData(userData.user_id, setUserData);
    }, 4000);

    return () => clearInterval(interval)
  }, [userData.user_id]);

  function handleLogout() {
    setUserData('');
    setIsLoggedIn(false);
  }
  
  const orderList = userData.orders.map(order => 
    <>
      <p>{order.order_id}: {order.side} {order.quantity} @ {order.limit} <button>Delete Order</button></p>
    </>
  );

  const tradeList = userData.trades.map(trade => 
    <p>{trade.buyer_name} {trade.seller_name} {trade.volume} LOTS @ {trade.price}</p>
  );

  return (
    <div className="column">
        <p>Username: {userData.username}</p>
        <p>User ID: {userData.user_id}</p>
        <p>Cash: {userData.cash}</p>
        <p>Position: {userData.position}</p>
        Orders: <ul>{orderList}</ul>
        Trades: <ul>{tradeList}</ul>
        <button onClick={handleLogout}>Logout</button>
      </div>
  )

}

function PriceHistory() {
  const [priceData, setPriceData] = useState({buy_p:[], buy_t:[], sell_p:[], sell_t:[]});

  useEffect(() => {
    const interval = setInterval(() => {
      requestPriceHistory(setPriceData);
    }, 4000);

    return () => clearInterval(interval)
  }, []);

  return (
    <Plot 
      data={[
        {
          x: priceData.buy_t.map((d) => new Date(d)),
          y: priceData.buy_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'green'},
          name: 'Buy aggressor'
        },
        {
          x: priceData.sell_t.map((d) => new Date(d)),
          y: priceData.sell_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'red'},
          name: 'Sell aggressor'
        }
      ]}
      layout={{
        title: 'Price History',
        xaxis: {
          title: 'Time'
        },
        yaxis: {
          title: 'Price'
        }
      }}
    />
  )
}

function LoggedInView({setUserData, userData, setIsLoggedIn}) {

  return (
    <>
    <div className="row">
      <UserDataPanel setUserData={setUserData} userData={userData} setIsLoggedIn={setIsLoggedIn}/>
      <div className="column">
        <BuyForm user_id={userData.user_id} setUserData={setUserData}/>
        <br></br>
        <SellForm user_id={userData.user_id} setUserData={setUserData}/>
        <br></br>
        <PriceHistory />
      </div>
      <div className="column">
      </div>
    </div>
    </>
  )
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState('');

  return (
    <div className="App">
      {
        isLoggedIn ? (
          <LoggedInView setUserData={setUserData} userData={userData} setIsLoggedIn={setIsLoggedIn} />
        ) : (
          <LoginForm setIsLoggedIn={setIsLoggedIn} setUserData={setUserData}/>
        )
      }
    </div>
  );
}

export default App;
