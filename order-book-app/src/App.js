import './App.css';
import {useState, useEffect} from 'react'
import Plot from 'react-plotly.js'

async function requestOrderBook(setOrderData) {
  const response = await fetch("http://127.0.0.1:5000/order-book");
  const data = await response.json();
  setOrderData(data);
}

async function requestUserData(user_id, setUserData) {
  const response = await fetch(`http://127.0.0.1:5000/user-data/${user_id}`);
  const data = await response.json();
  setUserData(data);
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
      await requestUserData(user_id, setUserData);
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

  async function handleDeleteOrder(order_id) {
    await fetch(`http://127.0.0.1:5000/delete-order/${order_id}`);
    await requestUserData(userData.user_id, setUserData);
  }
  
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
    <p>
      {order.order_id}: {order.side} {order.quantity} @ {order.limit} 
      <button onClick={() => handleDeleteOrder(order.order_id)}>Delete Order</button>
    </p>
  );

  const tradeList = userData.trades.map(trade => 
    <p>{trade.buyer_name} {trade.seller_name} {trade.volume} LOTS @ {trade.price}</p>
  );

  return (
    <>
      <p>Username: {userData.username}</p>
      <p>User ID: {userData.user_id}</p>
      <p>Cash: {userData.cash}</p>
      <p>Position: {userData.position}</p>
      Orders: <ul>{orderList}</ul>
      Trades: <ul>{tradeList}</ul>
      <button onClick={handleLogout}>Logout</button>
    </>
  )
}

function OrderBook() {
  const [orderData, setOrderData] = useState({'bids':[], 'asks':[]});

  useEffect(() => {
    const interval = setInterval(() => {
      requestOrderBook(setOrderData);
    }, 2000);

    return () => clearInterval(interval)
  }, []);


  return (
    <table>
      <thead>
        <tr>
          <th>Own Bid</th>
          <th>Bid Volume</th>
          <th>Price</th>
          <th>Ask Volume</th>
          <th>Own Ask</th>
        </tr>
      </thead>
      <tbody>

      </tbody>
    </table>
  )
}

function PriceHistory() {
  const [bboHistory, setBBOHistory] = useState(
    {
      bb_t:[], bb_p:[], bo_t:[], bo_p:[], /* Actual data points */
      bt:[], bp:[], ot:[], op:[], /* Contains extra points to aid graphing */
    });

  const [lastDones, setLastDones] = useState(
    {buy_t:[], buy_p:[], sell_t:[], sell_p:[]}
  );

  async function requestBBOHistory(index) {
    const response = await fetch(`http://127.0.0.1:5000/bbo-history/${index}`);
    const data = await response.json();

    setBBOHistory(prev => {
      return {
        bb_t: prev.bb_t.concat(data.bb_t),
        bb_p: prev.bb_p.concat(data.bb_p),
        bo_t: prev.bo_t.concat(data.bo_t),
        bo_p: prev.bo_p.concat(data.bo_p),
        bt: prev.bt.concat(data.bt),
        bp: prev.bp.concat(data.bp),
        ot: prev.ot.concat(data.ot),
        op: prev.op.concat(data.op),
      };
    });
  }
  
  async function requestLastDones(b_i, s_i) {
    const response = await fetch(`http://127.0.0.1:5000/last-dones/${b_i}/${s_i}`);
    const data = await response.json();
    setLastDones(prev => ({
      buy_t:[...prev.buy_t, ...data.buy_t],
      buy_p:[...prev.buy_p, ...data.buy_p],
      sell_t:[...prev.sell_t, ...data.sell_t],
      sell_p:[...prev.sell_p, ...data.sell_p]
    }));
  }  

  useEffect(() => {
    const interval = setInterval(() => {
      requestBBOHistory(bboHistory.bb_p.length);
      requestLastDones(lastDones.buy_p.length, lastDones.sell_p.length);
    }, 6000);

    return () => clearInterval(interval)
  }, [bboHistory, lastDones]);

  return (
    <Plot 
      data={[
        {
          x: lastDones.buy_t.map((d) => new Date(d)),
          y: lastDones.buy_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'green'},
          name: 'Last done buy aggressor',
        },
        {
          x: lastDones.sell_t.map((d) => new Date(d)),
          y: lastDones.sell_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'red'},
          name: 'Last done sell aggressor'
        },
        {
          x: bboHistory.bb_t.map((d) => new Date(d)),
          y: bboHistory.bb_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'purple'},
          name: 'BBO'
        },
        {
          x: bboHistory.bo_t.map((d) => new Date(d)),
          y: bboHistory.bo_p,
          type: 'scatter',
          mode: 'markers',
          marker: {color: 'purple'},
          showlegend: false
        },
        {
          x: bboHistory.bt.map((d) => new Date(d)),
          y: bboHistory.bp,
          type: 'scatter',
          mode: 'lines',
          marker: {color: 'purple'},
          showlegend: false,
          hoverinfo: 'skip'
        },
        {
          x: bboHistory.ot.map((d) => new Date(d)),
          y: bboHistory.op,
          type: 'scatter',
          mode: 'lines',
          marker: {color: 'purple'},
          showlegend: false,
          hoverinfo: 'skip'
        }
      ]}
      layout={{
        title: 'Price History',
        uirevision: true,
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
      <div className="column">
        <UserDataPanel setUserData={setUserData} userData={userData} setIsLoggedIn={setIsLoggedIn}/>
      </div>
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
    <div className="row">
      <div className="column">
        <OrderBook/>
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
