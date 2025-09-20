import { createApp } from 'vue'
import TradingDashboard from './components/TradingDashboard.vue'

const app = createApp({})

// Register global components
app.component('trading-dashboard', TradingDashboard)

// Mount the app
app.mount('#app')