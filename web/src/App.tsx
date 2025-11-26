import { BrowserRouter, Routes, Route } from 'react-router-dom'
import SearchScreen from './components/SearchScreen'
import ItemDetail from './components/ItemDetail'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<SearchScreen />} />
          <Route path="/item/:itemId" element={<ItemDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App

